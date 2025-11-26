"""
Database versioning and migration management system

Replaces manual migration scripts with a standardized versioning approach.
Tracks schema version and applies migrations idempotently.

Usage:
  from db_migrations import run_migrations
  run_migrations()  # Applied automatically on app startup
"""

import logging
from datetime import datetime
from pathlib import Path
from config import config

logger = logging.getLogger(__name__)

# Safe conditional imports for database drivers
try:
    import sqlite3
except ImportError:
    sqlite3 = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

DB_PATH = config.DB_PATH
CURRENT_SCHEMA_VERSION = 6


def get_db_placeholder(conn):
    """
    Get the correct parameter placeholder for the active database driver.
    
    DB-API 2.0 specifies that connections have a paramstyle attribute:
    - 'qmark': Question mark style (SQLite)
    - 'format': ANSI C printf format codes (PostgreSQL uses %s)
    - 'pyformat': Python extended format codes (:name)
    - 'numeric': Numeric positional style (:1, :2)
    - 'named': Named style (:name)
    
    Returns:
        str: The correct placeholder for this database driver
    """
    try:
        # Check against sqlite3 if available
        if sqlite3 is not None and isinstance(conn, sqlite3.Connection):
            return '?'
        
        # Check against psycopg2 if available
        if psycopg2 is not None and isinstance(conn, psycopg2.extensions.connection):
            return '%s'
        
        # Fallback: try to read paramstyle attribute
        if hasattr(conn, 'paramstyle'):
            paramstyle = conn.paramstyle
            if paramstyle == 'qmark':
                return '?'
            elif paramstyle == 'format':
                return '%s'
            elif paramstyle == 'pyformat':
                return '%(name)s'  # Would need to be handled specially
            else:
                logger.warning(f"Unknown paramstyle: {paramstyle}, defaulting to '%s'")
                return '%s'
    except Exception as e:
        logger.warning(f"Could not determine paramstyle: {e}, defaulting to '%s'")
    
    # Default to '%s' (PostgreSQL format) as it's more common in production
    return '%s'


def get_migration_conn():
    """Get a database connection for migrations"""
    from database import get_db_connection
    conn = get_db_connection()
    
    # Only apply WAL mode for SQLite
    if config.DATABASE_TYPE == 'sqlite':
        cursor = conn.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        conn.commit()
    
    return conn


def init_version_table(conn):
    """Create db_version table if missing"""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS db_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')
    conn.commit()


def get_current_version(conn):
    """Get current database schema version"""
    try:
        init_version_table(conn)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(version) FROM db_version')
        result = cursor.fetchone()
        return result[0] if result[0] else 0
    except Exception as e:
        logger.warning(f"Could not read db_version: {e}")
        return 0


def apply_migration(conn, version: int, description: str, migration_sql: str):
    """Apply a single migration
    
    Handles both SQLite and PostgreSQL by:
    - Using executescript for SQLite (handles multiple statements)
    - Splitting and executing individually for PostgreSQL
    - Using the correct parameter placeholder for each driver
    """
    cursor = conn.cursor()
    try:
        logger.info(f"Applying migration v{version}: {description}")
        
        # SQLite has executescript, PostgreSQL doesn't
        if config.DATABASE_TYPE == 'sqlite':
            cursor.executescript(migration_sql)
        else:
            # PostgreSQL: execute statements individually
            # Split by ';' but be careful with strings containing ';'
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    cursor.execute(stmt)
            conn.commit()
        
        # Use the correct placeholder for the active database driver
        placeholder = get_db_placeholder(conn)
        
        if placeholder == '?':
            # SQLite: question mark style
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (?, ?)
            ''', (version, description))
        else:
            # PostgreSQL and others: format style (%s)
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (%s, %s)
            ''', (version, description))
        
        conn.commit()
        logger.info(f"[OK] Migration v{version} applied successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Migration v{version} failed: {e}")
        conn.rollback()
        return False


def migration_v1(conn):
    """
    Migration V1: Unified table schema
    
    Creates:
    - watchlist
    - analysis_results (UNIFIED - replaces all_stocks_analysis)
    - analysis_jobs
    - db_version tracking table
    
    This is the initial production schema.
    """
    migration_sql = '''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE NOT NULL,
        name TEXT,
        user_id INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
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
    );
    
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
    );
    
    CREATE INDEX IF NOT EXISTS idx_ticker ON analysis_results(ticker);
    CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_results(created_at);
    CREATE INDEX IF NOT EXISTS idx_ticker_created ON analysis_results(ticker, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_symbol ON analysis_results(symbol);
    CREATE INDEX IF NOT EXISTS idx_yahoo_symbol ON analysis_results(yahoo_symbol);
    CREATE INDEX IF NOT EXISTS idx_status ON analysis_results(status);
    CREATE INDEX IF NOT EXISTS idx_analysis_source ON analysis_results(analysis_source);
    CREATE INDEX IF NOT EXISTS idx_symbol_created ON analysis_results(symbol, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_source_symbol ON analysis_results(analysis_source, symbol);
    CREATE INDEX IF NOT EXISTS idx_updated_at ON analysis_results(updated_at);
    CREATE INDEX IF NOT EXISTS idx_job_status ON analysis_jobs(status);
    '''
    
    return apply_migration(conn, 1, "Initial unified schema", migration_sql)


def migration_v2(conn):
    """
    Migration V2: Add ticker and notes columns to watchlist table
    
    Adds (conditionally):
    - ticker column (copy from symbol for existing rows)
    - notes column (for user annotations)
    
    This migration ensures backward compatibility with routes expecting ticker field.
    Detects existing columns and only adds missing ones.
    """
    cursor = conn.cursor()
    migration_sql_parts = []
    
    try:
        # Check for existing columns based on database type
        existing_columns = set()
        
        if config.DATABASE_TYPE == 'sqlite':
            # SQLite: Use PRAGMA table_info
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = cursor.fetchall()
            existing_columns = {col[1] for col in columns}  # col[1] is column name
            logger.debug(f"SQLite watchlist columns: {existing_columns}")
        else:
            # PostgreSQL: Use information_schema
            cursor.execute('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'watchlist'
            ''')
            columns = cursor.fetchall()
            existing_columns = {col[0] for col in columns}  # col[0] is column_name
            logger.debug(f"PostgreSQL watchlist columns: {existing_columns}")
        
        # Conditionally add ticker column
        if 'ticker' not in existing_columns:
            migration_sql_parts.append('ALTER TABLE watchlist ADD COLUMN ticker TEXT;')
            logger.info("  Will add ticker column")
        else:
            logger.info("  ticker column already exists, skipping")
        
        # Conditionally add notes column
        if 'notes' not in existing_columns:
            migration_sql_parts.append('ALTER TABLE watchlist ADD COLUMN notes TEXT;')
            logger.info("  Will add notes column")
        else:
            logger.info("  notes column already exists, skipping")
        
        # Always add the UPDATE to sync symbol->ticker if ticker column exists
        if 'ticker' in existing_columns or 'ticker' not in existing_columns:
            # Safe to add UPDATE even if column was just added
            migration_sql_parts.append('UPDATE watchlist SET ticker = symbol WHERE ticker IS NULL;')
        
        # Compose final SQL
        migration_sql = '\n'.join(migration_sql_parts)
        
        # If no changes needed, still record migration as applied
        if not migration_sql_parts or migration_sql.strip() == '':
            logger.info("Migration v2: No changes needed for watchlist table")
            # Record the migration as applied even if no SQL executed
            placeholder = get_db_placeholder(conn)
            if placeholder == '?':
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (?, ?)
                ''', (2, "Add ticker and notes to watchlist (no-op)"))
            else:
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (%s, %s)
                ''', (2, "Add ticker and notes to watchlist (no-op)"))
            conn.commit()
            return True
        
        return apply_migration(conn, 2, "Add ticker and notes to watchlist", migration_sql)
    
    except Exception as e:
        logger.error(f"✗ Migration v2 preparation failed: {e}")
        conn.rollback()
        return False


def migration_v3(conn):
    """
    Migration V3: Add constraints and indices for job tracking and performance
    
    This migration handles both PostgreSQL and SQLite:
    - Adds tickers_json column to analysis_jobs (both databases)
    - Adds indices for performance
    - Adds columns for job tracking and temporal data
    - Creates new tables for detailed tracking
    
    For PostgreSQL: Uses CAST(... AS DATE) and information_schema
    For SQLite: Uses PRAGMA table_info and simpler syntax
    """
    try:
        cursor = conn.cursor()
        
        logger.info("Running migration v3...")
        
        # UNIVERSAL: Add tickers_json column to analysis_jobs (both SQLite and PostgreSQL)
        try:
            if config.DATABASE_TYPE == 'postgres':
                # Check if column exists in PostgreSQL
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='analysis_jobs' AND column_name='tickers_json'
                """)
                if not cursor.fetchone():
                    cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
                    logger.info("  ✓ Added tickers_json column to analysis_jobs (PostgreSQL)")
            else:
                # SQLite: Check using PRAGMA table_info
                cursor.execute("PRAGMA table_info(analysis_jobs)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'tickers_json' not in columns:
                    cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
                    logger.info("  ✓ Added tickers_json column to analysis_jobs (SQLite)")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.debug(f"  tickers_json column already exists or error: {e}")
        
        # UNIVERSAL: Create index on (tickers_json, status) for both databases
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_tickers
                ON analysis_jobs(tickers_json, status)
            ''')
            conn.commit()
            logger.info("  ✓ Created index on (tickers_json, status)")
        except Exception as e:
            conn.rollback()
            logger.debug(f"  Index may already exist: {e}")
        
        # POSTGRESQL ONLY: Add constraints and additional indices
        if config.DATABASE_TYPE == 'postgres':
            logger.info("Running PostgreSQL-specific migration v3...")
        
            # 1. Add UNIQUE index on (ticker, date)
            try:
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                    ON analysis_results(ticker, CAST(created_at AS DATE))
                ''')
                conn.commit()
                logger.info("  ✓ UNIQUE INDEX created on (ticker, date)")
            except Exception as e:
                conn.rollback()
                logger.debug(f"  Index may already exist: {e}")
        
        # 2. Add basic indices
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol
                ON analysis_results(symbol)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                ON analysis_results(created_at DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON analysis_jobs(status, created_at DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_source
                ON analysis_results(analysis_source, created_at DESC)
            ''')
            conn.commit()
            logger.info("  ✓ Basic indices created")
        except Exception as e:
            conn.rollback()
            logger.debug(f"  Indices may already exist: {e}")
            
            # 3. Add columns to existing tables (PostgreSQL only)
            try:
                # Check existing columns in watchlist (PostgreSQL only)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='watchlist'
                """)
                existing_cols = {row[0] for row in cursor.fetchall()}
                
                if 'last_job_id' not in existing_cols:
                    cursor.execute('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT')
                    logger.info("  ✓ Added last_job_id column to watchlist")
                
                if 'last_analyzed_at' not in existing_cols:
                    cursor.execute('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP')
                    logger.info("  ✓ Added last_analyzed_at column to watchlist")
                
                if 'last_status' not in existing_cols:
                    cursor.execute('ALTER TABLE watchlist ADD COLUMN last_status TEXT')
                    logger.info("  ✓ Added last_status column to watchlist")
                
                conn.commit()
                logger.info("  ✓ All watchlist columns added")
            except Exception as e:
                conn.rollback()
                logger.debug(f"  Watchlist columns may already exist: {e}")
            
            try:
                # Check existing columns in analysis_results (PostgreSQL only)
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='analysis_results'
                """)
                existing_cols = {row[0] for row in cursor.fetchall()}
                
                if 'job_id' not in existing_cols:
                    cursor.execute('ALTER TABLE analysis_results ADD COLUMN job_id TEXT')
                    logger.info("  ✓ Added job_id column to analysis_results")
                
                if 'started_at' not in existing_cols:
                    cursor.execute('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP')
                    logger.info("  ✓ Added started_at column to analysis_results")
                
                if 'completed_at' not in existing_cols:
                    cursor.execute('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP')
                    logger.info("  ✓ Added completed_at column to analysis_results")
                
                conn.commit()
                logger.info("  ✓ All analysis_results columns added")
            except Exception as e:
                conn.rollback()
                logger.debug(f"  Analysis results columns may already exist: {e}")
        
        # 4. Create new tables (PostgreSQL only)
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_jobs_details (
                    id SERIAL PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, ticker)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_job_id
                ON analysis_jobs_details(job_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_ticker
                ON analysis_jobs_details(ticker)
            ''')
            
            conn.commit()
            logger.info("  ✓ Created analysis_jobs_details table")
        except Exception as e:
            conn.rollback()
            logger.debug(f"  analysis_jobs_details table may already exist: {e}")
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_raw_data (
                    id SERIAL PRIMARY KEY,
                    analysis_result_id INTEGER NOT NULL,
                    raw_indicators TEXT,
                    raw_signals TEXT,
                    raw_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_data_result_id
                ON analysis_raw_data(analysis_result_id)
            ''')
            
            conn.commit()
            logger.info("  ✓ Created analysis_raw_data table")
        except Exception as e:
            conn.rollback()
            logger.debug(f"  analysis_raw_data table may already exist: {e}")
        
        # 5. Add composite indices
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol_date
                ON analysis_results(symbol, CAST(created_at AS DATE) DESC)
            ''')
            logger.info("  ✓ Created composite indices")
        except Exception as e:
            logger.debug(f"  Composite indices may already exist: {e}")
        
        conn.commit()
        logger.info("[OK] Migration v3 completed successfully")
        
        # Use the centralized helper so migration bookkeeping follows the
        # same error handling and logging as all other migrations.
        migration_sql = """
        -- PostgreSQL constraints, indices, and job tracking
        -- (No-op here because we've already applied the statements above.)
        """

        # apply_migration will insert the db_version record and commit/rollback
        # using the same param style detection implemented there.
        return apply_migration(conn, 3, "PostgreSQL constraints, indices, and job tracking", migration_sql)
        
    except Exception as e:
        logger.error(f"Migration v3 failed: {e}")
        conn.rollback()
        return False


def migration_v4(conn):
    """
    Migration V4: Rename 'symbol' column to 'ticker' in watchlist table
    
    This migration safely renames the symbol column to ticker for consistency
    across the codebase (analysis_results uses ticker).
    
    Strategy:
    1. Clean and validate data before migration
    2. Create new table with correct schema (ticker instead of symbol)
    3. Copy data from old table
    4. Drop old table
    5. Rename new table
    6. Recreate indices
    
    Works for both SQLite and PostgreSQL
    """
    try:
        cursor = conn.cursor()
        
        logger.info("Running migration v4: Rename 'symbol' to 'ticker' in watchlist table...")
        
        # STEP 1: Validate and clean data before migration
        logger.info("  [Step 1] Validating watchlist data...")
        try:
            # Get stats before migration
            cursor.execute("SELECT COUNT(*) FROM watchlist")
            count_before = cursor.fetchone()[0]
            logger.info(f"    Total records: {count_before}")
            
            # Check for NULL values in symbol
            cursor.execute("SELECT COUNT(*) FROM watchlist WHERE symbol IS NULL")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                logger.warning(f"    Found {null_count} records with NULL symbol - removing them")
                cursor.execute("DELETE FROM watchlist WHERE symbol IS NULL")
                conn.commit()
                logger.info(f"    ✓ Removed {null_count} records with NULL symbol")
            
            # Check for duplicates and clean them
            cursor.execute("""
                SELECT COUNT(*) FROM watchlist 
                WHERE id NOT IN (
                    SELECT MIN(id) FROM watchlist GROUP BY LOWER(symbol)
                )
            """)
            dup_count = cursor.fetchone()[0]
            if dup_count > 0:
                logger.warning(f"    Found {dup_count} duplicate records - removing them")
                cursor.execute("""
                    DELETE FROM watchlist 
                    WHERE id NOT IN (
                        SELECT MIN(id) FROM watchlist GROUP BY LOWER(symbol)
                    )
                """)
                conn.commit()
                logger.info(f"    ✓ Removed {dup_count} duplicate records")
            
            # Trim whitespace from symbol values
            if config.DATABASE_TYPE == 'postgres':
                cursor.execute("UPDATE watchlist SET symbol = TRIM(symbol) WHERE symbol IS NOT NULL")
            else:
                cursor.execute("UPDATE watchlist SET symbol = TRIM(symbol) WHERE symbol IS NOT NULL")
            conn.commit()
            logger.info("    ✓ Trimmed whitespace from symbol values")
            
        except Exception as e:
            logger.warning(f"    Data validation warning: {e}")
            conn.rollback()
        
        # STEP 2: Check if migration is needed (ticker column might already exist)
        logger.info("  [Step 2] Checking if ticker column already exists...")
        
        ticker_exists = False
        symbol_exists = False
        
        if config.DATABASE_TYPE == 'postgres':
            # PostgreSQL: check information_schema
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='watchlist' AND column_name='ticker'
            """)
            ticker_exists = cursor.fetchone() is not None
            
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='watchlist' AND column_name='symbol'
            """)
            symbol_exists = cursor.fetchone() is not None
            
            logger.info(f"    ticker column exists: {ticker_exists}")
            logger.info(f"    symbol column exists: {symbol_exists}")
        else:
            # SQLite: check PRAGMA table_info
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = {row[1] for row in cursor.fetchall()}
            ticker_exists = 'ticker' in columns
            symbol_exists = 'symbol' in columns
            logger.info(f"    ticker column exists: {ticker_exists}")
            logger.info(f"    symbol column exists: {symbol_exists}")
        
        # If migration already done, skip
        if ticker_exists and not symbol_exists:
            logger.info("    ✓ Migration already applied (ticker exists, symbol doesn't)")
            return apply_migration(conn, 4, "Rename symbol to ticker in watchlist (already done)", "")
        
        # If only symbol exists, need to rename
        if symbol_exists and not ticker_exists:
            logger.info("    ✓ Migration needed: symbol exists, ticker doesn't")
        elif ticker_exists and symbol_exists:
            logger.warning("    Both ticker and symbol columns exist - removing symbol column")
        
        # STEP 3: Handle the rename based on database type
        logger.info("  [Step 3] Performing column rename...")
        
        try:
            if config.DATABASE_TYPE == 'postgres':
                # PostgreSQL: Use RENAME COLUMN
                if symbol_exists and not ticker_exists:
                    logger.info("    Executing: ALTER TABLE watchlist RENAME COLUMN symbol TO ticker")
                    cursor.execute("ALTER TABLE watchlist RENAME COLUMN symbol TO ticker")
                    logger.info("    ✓ Column renamed successfully")
                elif ticker_exists and symbol_exists:
                    logger.info("    Dropping duplicate symbol column (ticker already exists)")
                    cursor.execute("ALTER TABLE watchlist DROP COLUMN symbol")
                    logger.info("    ✓ Duplicate symbol column dropped")
            else:
                # SQLite: No RENAME COLUMN support, must recreate table
                logger.info("    Creating new table with ticker column...")
                
                # 1. Create backup of original table
                cursor.execute("""
                    CREATE TABLE watchlist_backup AS 
                    SELECT * FROM watchlist
                """)
                logger.info("    ✓ Created backup table")
                
                # 2. Drop old table
                cursor.execute("DROP TABLE watchlist")
                logger.info("    ✓ Dropped original watchlist table")
                
                # 3. Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE watchlist (
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
                logger.info("    ✓ Created new watchlist table with ticker column")
                
                # 4. Copy data from backup (symbol -> ticker)
                cursor.execute("""
                    INSERT INTO watchlist (id, ticker, name, user_id, created_at, last_job_id, last_analyzed_at, last_status, notes)
                    SELECT 
                        id,
                        symbol AS ticker,
                        name,
                        user_id,
                        created_at,
                        CASE WHEN json_extract(symbol, '$') IS NOT NULL THEN symbol ELSE NULL END,
                        NULL,
                        NULL,
                        NULL
                    FROM watchlist_backup
                """)
                logger.info(f"    ✓ Copied {cursor.rowcount} records from backup")
                
                # 5. Drop backup table
                cursor.execute("DROP TABLE watchlist_backup")
                logger.info("    ✓ Dropped backup table")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"    ✗ Column rename failed: {e}")
            conn.rollback()
            raise
        
        # STEP 4: Verify migration succeeded
        logger.info("  [Step 4] Verifying migration...")
        
        if config.DATABASE_TYPE == 'postgres':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='watchlist'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = [row[1] for row in cursor.fetchall()]
        
        logger.info(f"    Watchlist columns after migration: {columns}")
        
        if 'ticker' not in columns:
            raise Exception("Migration failed: 'ticker' column not found after migration")
        
        logger.info("    ✓ Migration verified successfully")
        
        # STEP 5: Recreate indices
        logger.info("  [Step 5] Recreating indices...")
        
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_created ON watchlist(created_at DESC)")
            logger.info("    ✓ Indices recreated")
        except Exception as e:
            logger.warning(f"    Index creation warning: {e}")
        
        conn.commit()
        
        logger.info("[OK] Migration v4 completed successfully")
        return apply_migration(conn, 4, "Rename symbol to ticker in watchlist", "")
        
    except Exception as e:
        logger.error(f"✗ Migration v4 failed: {e}")
        conn.rollback()
        return False


def migration_v5(conn):
    """
    Migration V5: Rename symbol to ticker (force rename if not already done)
    
    This migration ensures the watchlist table has 'ticker' instead of 'symbol'.
    It's designed to handle cases where migration v4 didn't run.
    """
    try:
        cursor = conn.cursor()
        logger.info("Running migration v5: Ensure watchlist has 'ticker' column...")
        
        # Check current columns
        if config.DATABASE_TYPE == 'postgres':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='watchlist'
                ORDER BY ordinal_position
            """)
            columns = {row[0] for row in cursor.fetchall()}
        else:
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = {row[1] for row in cursor.fetchall()}
        
        logger.info(f"Current watchlist columns: {columns}")
        
        # If already has ticker and no symbol, migration already done
        if 'ticker' in columns and 'symbol' not in columns:
            logger.info("✓ Migration already applied (ticker exists, symbol removed)")
            return apply_migration(conn, 5, "Ensure ticker column exists (already done)", "")
        
        # If has symbol but no ticker, need to rename
        if 'symbol' in columns and 'ticker' not in columns:
            logger.info("Column rename needed: symbol -> ticker")
            
            if config.DATABASE_TYPE == 'postgres':
                logger.info("Using PostgreSQL: ALTER TABLE RENAME COLUMN")
                cursor.execute("ALTER TABLE watchlist RENAME COLUMN symbol TO ticker")
                conn.commit()
            else:
                logger.info("Using SQLite: Recreate table")
                cursor.execute("CREATE TABLE watchlist_backup AS SELECT * FROM watchlist")
                cursor.execute("DROP TABLE watchlist")
                cursor.execute('''
                    CREATE TABLE watchlist (
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
                cursor.execute("""
                    INSERT INTO watchlist (id, ticker, name, user_id, created_at)
                    SELECT id, symbol, name, user_id, created_at FROM watchlist_backup
                """)
                cursor.execute("DROP TABLE watchlist_backup")
                conn.commit()
            
            logger.info("✓ Column renamed successfully")
        
        # If has both, drop symbol (cleanup from partial migration)
        if 'ticker' in columns and 'symbol' in columns:
            logger.info("Both columns exist, dropping duplicate 'symbol'")
            if config.DATABASE_TYPE == 'postgres':
                cursor.execute("ALTER TABLE watchlist DROP COLUMN symbol")
            else:
                # SQLite requires table recreation
                cursor.execute("CREATE TABLE watchlist_backup AS SELECT id, ticker, name, user_id, created_at FROM watchlist")
                cursor.execute("DROP TABLE watchlist")
                cursor.execute('''
                    CREATE TABLE watchlist (
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
                cursor.execute("INSERT INTO watchlist SELECT * FROM watchlist_backup")
                cursor.execute("DROP TABLE watchlist_backup")
            conn.commit()
            logger.info("✓ Duplicate column removed")
        
        logger.info("[OK] Migration v5 completed successfully")
        return apply_migration(conn, 5, "Ensure watchlist.ticker column exists", "")
        
    except Exception as e:
        logger.error(f"✗ Migration v5 failed: {e}")
        conn.rollback()
        return False


def migration_v6(conn):
    """
    Migration V6: Verify and stabilize watchlist schema
    
    Final verification that watchlist table is in correct state.
    """
    try:
        cursor = conn.cursor()
        logger.info("Running migration v6: Stabilize watchlist schema...")
        
        # Verify schema
        if config.DATABASE_TYPE == 'postgres':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='watchlist'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(watchlist)")
            columns = [row[1] for row in cursor.fetchall()]
        
        logger.info(f"Final watchlist schema: {columns}")
        
        if 'ticker' not in columns:
            logger.error("✗ Migration v6 failed: 'ticker' column missing after v5!")
            conn.rollback()
            return False
        
        if 'symbol' in columns:
            logger.warning("⚠️  'symbol' column still exists, attempting removal...")
            if config.DATABASE_TYPE == 'postgres':
                try:
                    cursor.execute("ALTER TABLE watchlist DROP COLUMN symbol")
                    conn.commit()
                except:
                    logger.warning("Could not drop symbol column (may be in use)")
        
        # Recreate indices for performance
        try:
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_created ON watchlist(created_at DESC)")
            conn.commit()
            logger.info("✓ Indices created")
        except:
            logger.debug("Indices may already exist")
        
        logger.info("[OK] Migration v6 completed successfully")
        return apply_migration(conn, 6, "Verify and stabilize watchlist schema", "")
        
    except Exception as e:
        logger.error(f"✗ Migration v6 failed: {e}")
        conn.rollback()
        return False


def run_migrations():
    """
    Run all pending migrations
    
    This is the main entry point. Call on app startup to ensure schema is current.
    Safe to call multiple times (idempotent).
    """
    import os
    
    # Only create directories for SQLite
    if config.DATABASE_TYPE == 'sqlite' and DB_PATH:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_migration_conn()
    try:
        init_version_table(conn)
        current_version = get_current_version(conn)
        
        logger.info(f"Current database version: {current_version}")
        logger.info(f"Target database version: {CURRENT_SCHEMA_VERSION}")
        
        if current_version < 1:
            migration_v1(conn)
        
        if current_version < 2:
            migration_v2(conn)
        
        if current_version < 3:
            migration_v3(conn)
        
        if current_version < 4:
            migration_v4(conn)
        
        if current_version < 5:
            migration_v5(conn)
        
        if current_version < 6:
            migration_v6(conn)
        
        # Cleanup: Remove duplicate watchlist entries
        try:
            logger.info("Cleaning up duplicate watchlist entries...")
            cursor = conn.cursor()
            
            # Determine which column to use (ticker or symbol)
            col_name = 'ticker'
            if config.DATABASE_TYPE == 'postgres':
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='watchlist' AND column_name='ticker'
                """)
                if not cursor.fetchone():
                    col_name = 'symbol'
            else:
                cursor.execute("PRAGMA table_info(watchlist)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'ticker' not in columns:
                    col_name = 'symbol'
            
            logger.info(f"  Using column: {col_name}")
            
            # Find and count duplicates
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT LOWER({col_name})) as unique_count
                FROM watchlist
            """)
            stats = cursor.fetchone()
            if stats:
                total = stats[0] if isinstance(stats, (tuple, list)) else stats.get('total', 0)
                unique = stats[1] if isinstance(stats, (tuple, list)) else stats.get('unique_count', 0)
                logger.info(f"  Watchlist stats: {total} total entries, {unique} unique entries")
                
                if total > unique:
                    logger.warning(f"  Found {total - unique} duplicate entries")
                    
                    # Delete duplicates, keeping the oldest (MIN id)
                    cursor.execute(f"""
                        DELETE FROM watchlist 
                        WHERE id NOT IN (
                            SELECT MIN(id) FROM watchlist GROUP BY LOWER({col_name})
                        )
                    """)
                    deleted_count = cursor.rowcount
                    logger.info(f"  ✓ Cleaned up {deleted_count} duplicate watchlist entries")
                else:
                    logger.info("  No duplicates found in watchlist")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning(f"Warning during watchlist cleanup: {e}")
        
        # CRITICAL: Ensure tickers_json column exists (added after v3 was already deployed)
        # This runs regardless of version to fix existing databases
        try:
            cursor = conn.cursor()
            if config.DATABASE_TYPE == 'postgres':
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='analysis_jobs' AND column_name='tickers_json'
                """)
                if not cursor.fetchone():
                    logger.info("Adding missing tickers_json column to analysis_jobs...")
                    cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
                    logger.info("  ✓ tickers_json column added to analysis_jobs")
            else:
                # SQLite
                cursor.execute("PRAGMA table_info(analysis_jobs)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'tickers_json' not in columns:
                    logger.info("Adding missing tickers_json column to analysis_jobs...")
                    cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
                    logger.info("  ✓ tickers_json column added to analysis_jobs")
            
            # Also create the index if it doesn't exist
            try:
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_job_tickers
                    ON analysis_jobs(tickers_json, status)
                ''')
                logger.info("  ✓ Index on (tickers_json, status) verified")
            except:
                pass  # Index may already exist
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning(f"Error ensuring tickers_json column: {e}")
        
        current_version = get_current_version(conn)
        if current_version == CURRENT_SCHEMA_VERSION:
            logger.info("[OK] Database schema is up to date")
            return True
        else:
            logger.error(f"[ERROR] Database version mismatch: {current_version} != {CURRENT_SCHEMA_VERSION}")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s'
    )
    success = run_migrations()
    sys.exit(0 if success else 1)
