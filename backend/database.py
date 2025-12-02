import os
import sqlite3
import logging
import time
from flask import g
from config import config

# Setup module logger
logger = logging.getLogger(__name__)

# Database type detection
DB_PATH = config.DB_PATH
DATABASE_TYPE = config.DATABASE_TYPE

# Module-level initialization status flag
db_initialized = False

# Retry configuration
DB_INIT_MAX_ATTEMPTS = 3
DB_INIT_BACKOFF_BASE = 2  # seconds (exponential backoff: 2, 4, 8)

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
            # Enable WAL mode for better concurrency (SQLite only)
            cursor = g.db.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA synchronous=NORMAL')
            cursor.close()
    return g.db

def _convert_query_params(query, args, database_type=None):
    """
    Convert SQL query parameters between SQLite (?) and PostgreSQL (%s) formats.
    
    This function ensures queries work with both databases by converting
    SQLite placeholder style (?) to the correct format for the target database.
    
    Args:
        query: SQL query with placeholders
        args: Tuple of query arguments
        database_type: 'sqlite' or 'postgres' (auto-detected if None)
    
    Returns:
        (converted_query, args): Query with correct placeholders and args
    """
    if database_type is None:
        database_type = DATABASE_TYPE
    
    if database_type == 'postgres':
        # Convert ? placeholders to %s for PostgreSQL
        # This is safe as long as ? doesn't appear in string literals
        converted = query.replace('?', '%s')
        return converted, args
    else:
        # SQLite already uses ?, no conversion needed
        return query, args


def query_db(query, args=(), one=False):
    """Query database and return results"""
    # Convert query parameters for current database
    query, args = _convert_query_params(query, args)
    db = get_db()
    
    # Handle both SQLite and PostgreSQL connection types
    if DATABASE_TYPE == 'postgres':
        # PostgreSQL: need to create cursor explicitly
        cur = db.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
    else:
        # SQLite: can call execute directly on connection
        cur = db.execute(query, args)
        rv = cur.fetchall()
        cur.close()
    
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute database modification and return last row ID"""
    # Convert query parameters for current database
    query, args = _convert_query_params(query, args)
    db = get_db()
    
    # Handle both SQLite and PostgreSQL connection types
    if DATABASE_TYPE == 'postgres':
        # PostgreSQL: need to create cursor explicitly
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()
        # Note: PostgreSQL doesn't have lastrowid; return None or use RETURNING clause
        return None
    else:
        # SQLite: can call execute directly on connection
        cur = db.execute(query, args)
        db.commit()
        return cur.lastrowid


# Thread-safe database functions for background tasks
def get_db_connection():
    """Get a new database connection (not Flask g-based)"""
    if DATABASE_TYPE == 'postgres':
        return psycopg2.connect(config.DATABASE_URL)
    else:
        # ✅ FIX #13: Add timeout for sqlite3 (wait up to 5 seconds for locks)
        return sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5.0)


def get_db_session():
    """Get a thread-safe database session as context manager"""
    from contextlib import contextmanager

    @contextmanager
    def session():
        conn = get_db_connection()
        if DATABASE_TYPE == 'sqlite':
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA synchronous=NORMAL')
            # ✅ FIX #13b: Add PRAGMA busy_timeout to handle lock contention (5 second timeout)
            cursor.execute('PRAGMA busy_timeout=5000')
            cursor.close()
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
    Execute a database query using correct parameter style for current database.
    
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
    """
    Initialize database schema for both SQLite and PostgreSQL with retry logic.
    
    Implements exponential backoff for transient failures (connection timeouts, 
    temporary unavailability). Re-raises critical non-transient errors immediately
    (authentication failures, invalid credentials, configuration errors).
    
    Sets module-level db_initialized flag on success for other code to check.
    
    Raises:
        Exception: For critical non-transient errors (auth failures, config errors)
    """
    global db_initialized
    
    logger.info(f"Initializing {DATABASE_TYPE} database (max {DB_INIT_MAX_ATTEMPTS} attempts with {DB_INIT_BACKOFF_BASE}s backoff base)")
    
    last_error = None
    
    for attempt in range(1, DB_INIT_MAX_ATTEMPTS + 1):
        try:
            if DATABASE_TYPE == 'postgres':
                _init_postgres_db()
            else:
                _init_sqlite_db()
            
            # Success: set initialization flag and log
            db_initialized = True
            logger.info(f"Database initialization successful on attempt {attempt}")
            return
        
        except (ConnectionError, TimeoutError, OSError, sqlite3.OperationalError) as e:
            # Transient failures: connection timeouts, temporary unavailability
            last_error = e
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
        
        except Exception as e:
            # Handle all exceptions with branching based on database type and error characteristics
            # Transient PostgreSQL connection errors get backoff/retry logic
            if DATABASE_TYPE == 'postgres' and isinstance(e, psycopg2.OperationalError) and 'could not connect' in str(e).lower():
                # Transient PostgreSQL connection error: retry with backoff
                last_error = e
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
                # Non-transient error (auth failure, config error, or non-PostgreSQL error): fail fast
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


def _init_sqlite_db():
    """Initialize SQLite database schema"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Watchlist table (with user_id for future multi-user support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            position_size INTEGER DEFAULT 0,
            risk_reward_ratio REAL DEFAULT 0,
            analysis_config TEXT,
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
            tickers_json TEXT,
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
    # NOTE: Removed all indexes from analysis_jobs due to tickers_json column causing 8KB index limit overflow
    # Removed: idx_job_status, idx_job_tickers, idx_job_tickers_hash, idx_jobs_status
    # Job status queries will use table scan (acceptable - analysis_jobs is small table, typically <100 rows)

    
    conn.commit()
    conn.close()
    
    # Use structured logging for initialization feedback
    logger.debug("SQLite database initialized successfully")


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
                analysis_source TEXT
            )
        ''')
        
        # Add columns if they don't exist (migration for existing databases)
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS position_size INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS risk_reward_ratio REAL DEFAULT 0")
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS analysis_config TEXT")
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
        # NOTE: Removed idx_job_status from analysis_jobs due to tickers_json column causing 8KB index limit overflow
        # Job status queries will use table scan (acceptable - analysis_jobs is small table, typically <100 rows)
        
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
        
    Note: This function replaces both cleanup_old_analyses() and cleanup_all_stocks_analysis()
          after migration to unified table architecture.
    """
    with get_db_session() as (conn, cursor):
        if ticker:
            # Cleanup by ticker (watchlist-style, backward compatible)
            query = '''
                DELETE FROM analysis_results
                WHERE ticker = ?
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE ticker = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            '''
            query, args = _convert_query_params(query, (ticker, ticker, keep_last))
            cursor.execute(query, args)
        elif symbol:
            # Cleanup by symbol (bulk analysis style, preferred for unified table)
            query = '''
                DELETE FROM analysis_results
                WHERE symbol = ?
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE symbol = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            '''
            query, args = _convert_query_params(query, (symbol, symbol, keep_last))
            cursor.execute(query, args)
        else:
            # Cleanup all symbols (works for both ticker and symbol)
            query = 'SELECT DISTINCT COALESCE(symbol, ticker) FROM analysis_results'
            query, args = _convert_query_params(query, ())
            cursor.execute(query, args)
            identifiers = [row[0] for row in cursor.fetchall()]
            
            for identifier in identifiers:
                delete_query = '''
                    DELETE FROM analysis_results
                    WHERE (symbol = ? OR ticker = ?)
                    AND id NOT IN (
                        SELECT id FROM analysis_results
                        WHERE (symbol = ? OR ticker = ?)
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                '''
                delete_query, delete_args = _convert_query_params(delete_query, (identifier, identifier, identifier, identifier, keep_last))
                cursor.execute(delete_query, delete_args)
        
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
    global db_initialized
    
    db_existed = os.path.exists(DB_PATH) if DATABASE_TYPE == 'sqlite' else True
    try:
        init_db()
        return db_existed
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
