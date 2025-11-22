import sqlite3
import os
from contextlib import contextmanager
from flask import g
from config import config

# CRITICAL FIX (ISSUE_019): Use centralized configuration
DB_PATH = config.DB_PATH

# Database connection constants
DB_LOCK_TIMEOUT = 30.0  # seconds - timeout for lock acquisition
DB_WAL_MODE = 'WAL'     # Write-Ahead Logging for better concurrency
DB_SYNC_MODE = 'NORMAL' # Balance safety and performance

def get_db_connection():
    """
    Get request-scoped database connection.
    Creates a new connection per Flask request using Flask's 'g' object.

    CRITICAL FIX: Thread-local storage doesn't work across Gunicorn workers (processes).
    Using Flask's g object ensures each HTTP request gets a fresh connection.

    Returns:
        sqlite3.Connection: Request-scoped database connection
    """
    # Check if current request already has a connection
    if 'db' not in g:
        # Create new connection for this request
        conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,  # Allow multi-threading (Gunicorn workers)
            timeout=DB_LOCK_TIMEOUT
        )
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrent read performance
        conn.execute(f'PRAGMA journal_mode={DB_WAL_MODE}')
        conn.execute(f'PRAGMA synchronous={DB_SYNC_MODE}')
        g.db = conn

    return g.db


@contextmanager
def get_db_session():
    """
    Context manager for database transactions with automatic commit/rollback.
    Ensures proper cleanup even if exceptions occur.
    
    Usage:
        with get_db_session() as (conn, cursor):
            cursor.execute(...)
            # Auto-commits on success, auto-rolls back on exception
    
    Yields:
        tuple: (connection, cursor)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        # Note: We don't close the connection here as it's reused within the thread
        cursor.close()


def close_db_connection(error):
    """
    Close the database connection for the current request.
    Called automatically by Flask after each request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database schema"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Watchlist table (with user_id for future multi-user support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            user_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analysis results table (UNIFIED - stores all analysis from watchlist AND bulk)
    # MIGRATION NOTE: Replaced dual-table architecture (analysis_results + all_stocks_analysis)
    # with single unified table. See DB_ARCHITECTURE.md for details.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            yahoo_symbol TEXT,
            score REAL NOT NULL,
            verdict TEXT NOT NULL,
            entry REAL,
            stop_loss REAL,
            target REAL,
            entry_method TEXT,
            data_source TEXT,
            is_demo_data BOOLEAN DEFAULT 0,
            raw_data TEXT,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            analysis_source TEXT
        )
    ''')
    
    # Job tracking table for async tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            successful INTEGER DEFAULT 0,
            errors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # Create indexes for faster queries on unified analysis_results table
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON analysis_results(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_results(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_created ON analysis_results(ticker, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON analysis_results(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_yahoo_symbol ON analysis_results(yahoo_symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON analysis_results(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_source ON analysis_results(analysis_source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_created ON analysis_results(symbol, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_symbol ON analysis_results(analysis_source, symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_updated_at ON analysis_results(updated_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_status ON analysis_jobs(status)')

    
    conn.commit()
    conn.close()
    
    # Use print for startup feedback (before logger is initialized)
    print("Database initialized successfully")


def cleanup_old_analyses(ticker=None, symbol=None, keep_last=10):
    """
    Keep only the last N analyses per stock using thread-safe connections.
    Works with unified analysis_results table for both watchlist and bulk analyses.
    
    Args:
        ticker: Specific ticker to cleanup (e.g., "RELIANCE.NS" - for backward compatibility)
        symbol: Specific symbol to cleanup (e.g., "RELIANCE" - preferred method)
        keep_last: Number of analyses to keep per stock (default 10)
        
    Returns:
        int: Number of records deleted
        
    Note: This function replaces both cleanup_old_analyses() and cleanup_all_stocks_analysis()
          after migration to unified table architecture.
    """
    with get_db_session() as (conn, cursor):
        if ticker:
            # Cleanup by ticker (watchlist-style, backward compatible)
            cursor.execute('''
                DELETE FROM analysis_results
                WHERE ticker = ?
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE ticker = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            ''', (ticker, ticker, keep_last))
        elif symbol:
            # Cleanup by symbol (bulk analysis style, preferred for unified table)
            cursor.execute('''
                DELETE FROM analysis_results
                WHERE symbol = ?
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE symbol = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            ''', (symbol, symbol, keep_last))
        else:
            # Cleanup all symbols (works for both ticker and symbol)
            cursor.execute('SELECT DISTINCT COALESCE(symbol, ticker) FROM analysis_results')
            identifiers = [row[0] for row in cursor.fetchall()]
            
            for identifier in identifiers:
                cursor.execute('''
                    DELETE FROM analysis_results
                    WHERE (symbol = ? OR ticker = ?)
                    AND id NOT IN (
                        SELECT id FROM analysis_results
                        WHERE (symbol = ? OR ticker = ?)
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                ''', (identifier, identifier, identifier, identifier, keep_last))
        
        deleted = cursor.rowcount
    
    return deleted


# Deprecated: kept for backward compatibility, now redirects to cleanup_old_analyses()
def cleanup_all_stocks_analysis(symbol=None, keep_last=10):
    """
    DEPRECATED: Use cleanup_old_analyses(symbol=...) instead.
    
    This function is kept for backward compatibility after migration to unified table.
    It now redirects to cleanup_old_analyses() which handles the unified table.
    """
    return cleanup_old_analyses(symbol=symbol, keep_last=keep_last)
