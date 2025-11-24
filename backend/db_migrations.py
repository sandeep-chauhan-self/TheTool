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
    Migration V4: Add tickers_hash column and replace tickers_json index
    
    Problem: PostgreSQL B-tree index size limit (8KB per row) exceeded when
    indexing tickers_json column containing 2,192+ stocks (~50KB).
    
    Solution: Use SHA-256 hash of tickers_json (fixed 64 bytes) for indexing.
    
    Changes:
    - Add tickers_hash column to analysis_jobs
    - Compute hashes for all existing jobs (backfill)
    - Drop old problematic index: idx_job_tickers(tickers_json, status)
    - Create new hash-based index: idx_job_tickers_hash(tickers_hash, status)
    
    Backward Compatibility: Keeps tickers_json unchanged, only affects internal queries
    """
    try:
        from migrations.add_tickers_hash import run_migration
        
        logger.info("Running migration v4 (Add tickers_hash column)...")
        
        # Call the dedicated migration module
        if run_migration(conn, config.DATABASE_TYPE):
            # Record migration as applied
            cursor = conn.cursor()
            placeholder = get_db_placeholder(conn)
            
            if placeholder == '?':
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (?, ?)
                ''', (4, "Add tickers_hash column and hash-based index"))
            else:
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (%s, %s)
                ''', (4, "Add tickers_hash column and hash-based index"))
            
            conn.commit()
            logger.info("[OK] Migration v4 completed successfully")
            return True
        else:
            logger.error("Migration v4 failed")
            return False
    except Exception as e:
        logger.error(f"Migration v4 failed: {e}")
        conn.rollback()
        return False


def migration_v5(conn):
    """
    Migration V5: Fix duplicate key constraint for re-analysis
    
    Problem: UNIQUE index on (ticker, date) prevents re-analyzing the same
    stock on the same day. This breaks "Analyze All Stocks" when run multiple
    times on the same day.
    
    Solution: Drop UNIQUE constraint, keep regular indices for performance.
    
    Changes:
    - Drop idx_analysis_ticker_date (UNIQUE constraint)
    - Create idx_analysis_ticker_created (regular index)
    - Create idx_analysis_created_date (regular index)
    - Allows multiple analyses per stock per day
    
    Backward Compatibility: Data preserved, just constraint removed
    """
    try:
        from migrations.fix_duplicate_constraint import run_migration
        
        logger.info("Running migration v5 (Fix duplicate key constraint)...")
        
        # Call the dedicated migration module
        if run_migration(conn, config.DATABASE_TYPE):
            # Record migration as applied
            cursor = conn.cursor()
            placeholder = get_db_placeholder(conn)
            
            if placeholder == '?':
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (?, ?)
                ''', (5, "Fix duplicate key constraint for re-analysis"))
            else:
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (%s, %s)
                ''', (5, "Fix duplicate key constraint for re-analysis"))
            
            conn.commit()
            logger.info("[OK] Migration v5 completed successfully")
            return True
        else:
            logger.error("Migration v5 failed")
            return False
    except Exception as e:
        logger.error(f"Migration v5 failed: {e}")
        conn.rollback()
        return False


def migration_v6(conn):
    """
    Migration V6: Add analysis versioning system
    
    Problem: No way to track analysis history or distinguish between multiple
    analyses of the same stock. Previous analyses are lost when re-analyzing.
    
    Solution: Add version tracking to analysis_results table.
    
    Changes:
    - Add 'analysis_version' column to analysis_results (INTEGER, default 0)
    - Create index on (ticker, analysis_version DESC) for efficient queries
    - Add 'latest_analysis_version' to watchlist for tracking
    - Backfill existing data with version = 0
    
    Benefits:
    - Full audit trail of all analyses
    - Quick fetch of latest version (ORDER BY version DESC LIMIT 1)
    - Historical analysis comparisons
    - Data integrity and regulatory compliance
    
    Backward Compatibility: Existing queries still work (version 0), new queries
    can fetch latest version using simple ORDER BY clause
    """
    try:
        from migrations.add_analysis_version import migration_v6_sqlite, migration_v6_postgres
        
        logger.info("Running migration v6 (Add analysis versioning)...")
        
        # Call the appropriate database-specific migration
        if config.DATABASE_TYPE == 'postgres':
            success = migration_v6_postgres(conn)
        else:
            success = migration_v6_sqlite(conn)
        
        if success:
            # Record migration as applied
            cursor = conn.cursor()
            placeholder = get_db_placeholder(conn)
            
            if placeholder == '?':
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (?, ?)
                ''', (6, "Add analysis versioning system"))
            else:
                cursor.execute('''
                    INSERT INTO db_version (version, description)
                    VALUES (%s, %s)
                ''', (6, "Add analysis versioning system"))
            
            conn.commit()
            logger.info("[OK] Migration v6 completed successfully")
            return True
        else:
            logger.error("Migration v6 failed")
            return False
    except Exception as e:
        logger.error(f"Migration v6 failed: {e}")
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
            
            # Find and count duplicates
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT LOWER(symbol)) as unique_symbols
                FROM watchlist
            """)
            stats = cursor.fetchone()
            if stats:
                total = stats[0] if isinstance(stats, (tuple, list)) else stats.get('total', 0)
                unique = stats[1] if isinstance(stats, (tuple, list)) else stats.get('unique_symbols', 0)
                logger.info(f"  Watchlist stats: {total} total entries, {unique} unique symbols")
                
                if total > unique:
                    logger.warning(f"  Found {total - unique} duplicate entries")
                    
                    # Delete duplicates, keeping the oldest (MIN id)
                    cursor.execute("""
                        DELETE FROM watchlist 
                        WHERE id NOT IN (
                            SELECT MIN(id) FROM watchlist GROUP BY LOWER(symbol)
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
