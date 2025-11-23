import os
import sqlite3
from flask import g
from config import config

# Database type detection
DB_PATH = config.DB_PATH
DATABASE_TYPE = config.DATABASE_TYPE

# Import PostgreSQL support if needed
if DATABASE_TYPE == 'postgres':
    import psycopg2
    from psycopg2.extras import RealDictCursor

def get_db():
    """Get database connection for current request"""
    if 'db' not in g:
        if DATABASE_TYPE == 'postgres':
            g.db = psycopg2.connect(config.DATABASE_URL)
            g.db.autocommit = False
        else:
            g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
            g.db.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            g.db.execute('PRAGMA journal_mode=WAL')
            g.db.execute('PRAGMA synchronous=NORMAL')
    return g.db

def query_db(query, args=(), one=False):
    """Query database and return results"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute database modification and return last row ID"""
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


# Thread-safe database functions for background tasks
def get_db_connection():
    """Get a new database connection (not Flask g-based)"""
    if DATABASE_TYPE == 'postgres':
        return psycopg2.connect(config.DATABASE_URL)
    else:
        return sqlite3.connect(DB_PATH, check_same_thread=False)


def get_db_session():
    """Get a thread-safe database session as context manager"""
    from contextlib import contextmanager

    @contextmanager
    def session():
        conn = get_db_connection()
        if DATABASE_TYPE == 'sqlite':
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
        try:
            yield conn, conn.cursor()
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()
    return session()


def close_thread_connection():
    """Thread cleanup function - no-op for now since connections are managed by context managers"""
    pass


# Import app for teardown registration (after app is defined)
def register_teardown(app):
    @app.teardown_appcontext
    def close_db_connection(exception):
        """Close database connection at end of request"""
        db = g.pop('db', None)
        if db is not None:
            db.close()

def init_db():
    """Initialize database schema for both SQLite and PostgreSQL"""
    if DATABASE_TYPE == 'postgres':
        _init_postgres_db()
    else:
        _init_sqlite_db()


def _init_sqlite_db():
    """Initialize SQLite database schema"""
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
    print("SQLite database initialized successfully")


def _init_postgres_db():
    """Initialize PostgreSQL database schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Watchlist table (with user_id for future multi-user support)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT,
                user_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis results table (UNIFIED - stores all analysis from watchlist AND bulk)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id SERIAL PRIMARY KEY,
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
                is_demo_data BOOLEAN DEFAULT FALSE,
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
        print("PostgreSQL database initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"ERROR initializing PostgreSQL database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


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


def init_db_if_needed():
    """
    Safe database initialization: idempotent and gunicorn-safe.
    
    Checks if DB exists, creates if missing, applies schema (idempotent).
    Safe to call on every request and in every worker process.
    
    Returns:
        bool: True if DB already existed, False if newly created
    """
    db_existed = os.path.exists(DB_PATH)
    try:
        init_db()
        return db_existed
    except Exception as e:
        print(f"ERROR: init_db_if_needed failed: {e}")
        raise


def close_db(exception=None):
    """
    Flask teardown function: closes DB connection at end of request.
    Registered with app.teardown_appcontext.
    
    Args:
        exception: Exception from app context (provided by Flask teardown)
    """
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            print(f"ERROR closing database: {e}")
