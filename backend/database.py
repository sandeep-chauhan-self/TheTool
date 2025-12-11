"""
PostgreSQL Database Module for TheTool
======================================

This module provides all database operations for the application.
All connections use PostgreSQL (no SQLite support).

Usage:
    - Flask requests: Use get_db() for request-scoped connections
    - Background threads: Use get_db_session() context manager
    - Standalone scripts: Use get_db_connection() directly

All SQL queries should use ? placeholders (SQLite style) and they will
be automatically converted to %s (PostgreSQL style) by _convert_query_params().
"""

import logging
import time
from flask import g
from config import config

# PostgreSQL driver
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup module logger
logger = logging.getLogger(__name__)

# Module-level initialization status flag
db_initialized = False

# Retry configuration
DB_INIT_MAX_ATTEMPTS = 3
DB_INIT_BACKOFF_BASE = 2  # seconds (exponential backoff: 2, 4, 8)


def get_db():
    """Get database connection for current Flask request"""
    if 'db' not in g:
        g.db = psycopg2.connect(config.DATABASE_URL)
        g.db.autocommit = False
    return g.db


def _convert_query_params(query, args):
    """
    Convert SQL query parameters from SQLite (?) to PostgreSQL (%s) format.
    
    This function maintains backward compatibility with existing code that uses
    SQLite-style ? placeholders. All queries in the codebase should use ? 
    placeholders, and this function converts them to PostgreSQL %s format.
    
    Args:
        query: SQL query with ? placeholders
        args: Tuple of query arguments
    
    Returns:
        (converted_query, args): Query with %s placeholders and unchanged args
    """
    # Convert ? placeholders to %s for PostgreSQL
    converted = query.replace('?', '%s')
    return converted, args


def query_db(query, args=(), one=False):
    """Query database and return results"""
    query, args = _convert_query_params(query, args)
    db = get_db()
    
    cur = db.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    """Execute database modification and commit"""
    query, args = _convert_query_params(query, args)
    db = get_db()
    
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    cur.close()
    # Note: PostgreSQL doesn't have lastrowid like SQLite
    # Use RETURNING clause in your query if you need the inserted ID
    return None


# Thread-safe database functions for background tasks
def get_db_connection():
    """Get a new database connection (not Flask g-based)"""
    return psycopg2.connect(config.DATABASE_URL)


def get_db_session():
    """Get a thread-safe database session as context manager"""
    from contextlib import contextmanager

    @contextmanager
    def session():
        conn = get_db_connection()
        try:
            yield conn, conn.cursor()
            conn.commit()
        except Exception as e:
            logger.warning(f"Transaction rolled back due to error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    return session()


def execute_query(query, args=(), fetch_one=False):
    """
    Execute a database query with automatic parameter conversion.
    
    Converts SQLite-style (?) placeholders to PostgreSQL-style (%s) automatically.
    Useful for standalone queries outside of Flask request context.
    
    Args:
        query: SQL query with ? placeholders
        args: Tuple of query arguments
        fetch_one: If True, return single row; if False, return all rows
    
    Returns:
        Query result (single row, all rows, or None)
    """
    query, args = _convert_query_params(query, args)
    
    with get_db_session() as (conn, cursor):
        cursor.execute(query, args)
        if fetch_one:
            return cursor.fetchone()
        else:
            return cursor.fetchall()


def close_thread_connection():
    """Thread cleanup function - no-op since connections are managed by context managers"""
    pass


def register_teardown(app):
    """Register Flask teardown handler to close database connections"""
    @app.teardown_appcontext
    def close_db_connection(exception):
        """Close database connection at end of request"""
        db = g.pop('db', None)
        if db is not None:
            db.close()


def init_db():
    """
    Initialize PostgreSQL database schema with retry logic.
    
    Implements exponential backoff for transient failures (connection timeouts, 
    temporary unavailability). Re-raises critical non-transient errors immediately
    (authentication failures, invalid credentials, configuration errors).
    
    Sets module-level db_initialized flag on success for other code to check.
    
    Raises:
        Exception: For critical non-transient errors (auth failures, config errors)
    """
    global db_initialized
    
    logger.info(f"Initializing PostgreSQL database (max {DB_INIT_MAX_ATTEMPTS} attempts with {DB_INIT_BACKOFF_BASE}s backoff base)")
    
    for attempt in range(1, DB_INIT_MAX_ATTEMPTS + 1):
        try:
            _init_postgres_db()
            
            # Success: set initialization flag and log
            db_initialized = True
            logger.info(f"Database initialization successful on attempt {attempt}")
            return
        
        except (ConnectionError, TimeoutError, OSError) as e:
            # Transient failures: connection timeouts, temporary unavailability
            if attempt < DB_INIT_MAX_ATTEMPTS:
                backoff_seconds = DB_INIT_BACKOFF_BASE ** (attempt - 1)
                logger.warning(
                    f"Transient database error on attempt {attempt}/{DB_INIT_MAX_ATTEMPTS}: {type(e).__name__}: {e}. "
                    f"Retrying in {backoff_seconds}s..."
                )
                time.sleep(backoff_seconds)
            else:
                logger.error(
                    f"Database initialization failed after {DB_INIT_MAX_ATTEMPTS} attempts due to transient errors. "
                    f"Last error: {type(e).__name__}: {e}"
                )
                db_initialized = False
                raise
        
        except psycopg2.OperationalError as e:
            # PostgreSQL operational errors - check if transient
            if 'could not connect' in str(e).lower():
                # Transient PostgreSQL connection error: retry with backoff
                if attempt < DB_INIT_MAX_ATTEMPTS:
                    backoff_seconds = DB_INIT_BACKOFF_BASE ** (attempt - 1)
                    logger.warning(
                        f"PostgreSQL connection error on attempt {attempt}/{DB_INIT_MAX_ATTEMPTS}: {e}. "
                        f"Retrying in {backoff_seconds}s..."
                    )
                    time.sleep(backoff_seconds)
                else:
                    logger.error(
                        f"Database initialization failed after {DB_INIT_MAX_ATTEMPTS} attempts. "
                        f"Last error: {e}"
                    )
                    db_initialized = False
                    raise
            else:
                # Non-transient PostgreSQL error: fail fast
                _raise_critical_error(e)
        
        except Exception as e:
            # Non-transient error (auth failure, config error): fail fast
            _raise_critical_error(e)


def _raise_critical_error(error):
    """
    Detect and log critical non-transient database errors, then re-raise.
    
    Identifies authentication failures, invalid credentials, configuration errors,
    and other errors that should cause the app to fail fast rather than retry.
    
    Args:
        error: The exception to analyze and re-raise
        
    Raises:
        The original exception after logging details
    """
    global db_initialized
    db_initialized = False
    
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Detect critical error patterns
    critical_patterns = [
        'password',
        'authentication',
        'permission denied',
        'invalid user',
        'role does not exist',
        'could not determine',
        'unknown database',
        'access denied',
        'invalid credentials',
    ]
    
    is_critical = any(pattern in error_str for pattern in critical_patterns)
    
    if is_critical or 'psycopg2' in str(type(error).__module__):
        log_level = logging.CRITICAL if is_critical else logging.ERROR
        logger.log(
            log_level,
            f"CRITICAL database error (non-transient): {error_type}: {error}. "
            f"Check database credentials and configuration. Failing fast."
        )
    else:
        logger.error(f"Database initialization error: {error_type}: {error}")
    
    raise error


def _init_postgres_db():
    """Initialize PostgreSQL database schema"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Watchlist table (with user_id for future multi-user support)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                ticker TEXT UNIQUE NOT NULL,
                name TEXT,
                user_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_job_id TEXT,
                last_analyzed_at TIMESTAMP,
                last_status TEXT,
                notes TEXT
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
                position_size INTEGER DEFAULT 0,
                risk_reward_ratio REAL DEFAULT 0,
                analysis_config TEXT,
                entry_method TEXT,
                data_source TEXT,
                is_demo_data BOOLEAN DEFAULT FALSE,
                raw_data TEXT,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                analysis_source TEXT,
                strategy_id INTEGER DEFAULT 1
            )
        ''')
        
        # Add columns if they don't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS position_size INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS risk_reward_ratio REAL DEFAULT 0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS analysis_config TEXT")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS strategy_id INTEGER DEFAULT 1")
            cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS strategy_id INTEGER DEFAULT 1")
            conn.commit()
        except Exception as col_error:
            logger.debug(f"Columns may already exist: {col_error}")
            conn.rollback()
        
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
                tickers_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                strategy_id INTEGER DEFAULT 1
            )
        ''')
        
        # Strategies metadata table (code-defined strategies, DB stores metadata only)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default strategies if they don't exist
        cursor.execute('''
            INSERT INTO strategies (id, name, description, is_active)
            VALUES 
                (1, 'Strategy 1', 'Balanced Analysis - Equal weight to all 12 indicators', TRUE),
                (2, 'Strategy 2', 'Trend Following - Emphasizes MACD, ADX, EMA crossovers', TRUE),
                (3, 'Strategy 3', 'Mean Reversion - Emphasizes RSI, Bollinger Bands, Stochastic', TRUE),
                (4, 'Strategy 4', 'Momentum Breakout - Volume-confirmed momentum signals', TRUE)
            ON CONFLICT (id) DO NOTHING
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_strategy_id ON analysis_results(strategy_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_strategy_id ON analysis_jobs(strategy_id)')
        
        conn.commit()
        logger.debug("PostgreSQL database schema initialized successfully")
    except Exception as e:
        logger.error(f"ERROR initializing PostgreSQL database: {e}")
        if conn:
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.warning(f"Failed to rollback PostgreSQL connection: {rollback_error}")
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as close_error:
                logger.warning(f"Failed to close PostgreSQL cursor: {close_error}")
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.warning(f"Failed to close PostgreSQL connection: {close_error}")


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
    """
    with get_db_session() as (conn, cursor):
        if ticker:
            # Cleanup by ticker (watchlist-style, backward compatible)
            query = '''
                DELETE FROM analysis_results
                WHERE ticker = %s
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE ticker = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                )
            '''
            cursor.execute(query, (ticker, ticker, keep_last))
        elif symbol:
            # Cleanup by symbol (bulk analysis style, preferred for unified table)
            query = '''
                DELETE FROM analysis_results
                WHERE symbol = %s
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE symbol = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                )
            '''
            cursor.execute(query, (symbol, symbol, keep_last))
        else:
            # Cleanup all symbols (works for both ticker and symbol)
            cursor.execute('SELECT DISTINCT COALESCE(symbol, ticker) FROM analysis_results')
            identifiers = [row[0] for row in cursor.fetchall()]
            
            for identifier in identifiers:
                delete_query = '''
                    DELETE FROM analysis_results
                    WHERE (symbol = %s OR ticker = %s)
                    AND id NOT IN (
                        SELECT id FROM analysis_results
                        WHERE (symbol = %s OR ticker = %s)
                        ORDER BY created_at DESC
                        LIMIT %s
                    )
                '''
                cursor.execute(delete_query, (identifier, identifier, identifier, identifier, keep_last))
        
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
    
    Creates schema if missing (CREATE IF NOT EXISTS is idempotent).
    Safe to call on every request and in every worker process.
    
    Returns:
        bool: Always True for PostgreSQL (database always exists externally)
    """
    global db_initialized
    
    try:
        init_db()
        return True
    except Exception as e:
        logger.error(f"ERROR: init_db_if_needed failed: {e}")
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
            logger.error(f"ERROR closing database: {e}")
