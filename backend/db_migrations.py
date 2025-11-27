"""
Database versioning and migration management system (PostgreSQL only)

Tracks schema version and applies migrations idempotently.

Usage:
  from db_migrations import run_migrations
  run_migrations()  # Applied automatically on app startup
"""

import logging
from config import config

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 6


def get_migration_conn():
    """Get a PostgreSQL database connection for migrations"""
    from database import get_db_connection
    return get_db_connection()


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
    """Apply a single migration (PostgreSQL format with %s placeholders)"""
    cursor = conn.cursor()
    try:
        logger.info(f"Applying migration v{version}: {description}")
        
        # PostgreSQL: execute statements individually
        if migration_sql.strip():
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for stmt in statements:
                if stmt:
                    cursor.execute(stmt)
        
        # Record migration using PostgreSQL format
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
    Migration V1: Unified table schema (PostgreSQL)
    
    Creates:
    - watchlist
    - analysis_results (UNIFIED)
    - analysis_jobs
    """
    migration_sql = '''
    CREATE TABLE IF NOT EXISTS watchlist (
        id SERIAL PRIMARY KEY,
        ticker TEXT UNIQUE NOT NULL,
        name TEXT,
        user_id INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
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
    CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_results(created_at DESC);
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
    Migration V2: Add watchlist columns (ticker, notes, tracking fields)
    """
    cursor = conn.cursor()
    try:
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'watchlist'
        """)
        existing_cols = {row[0] for row in cursor.fetchall()}
        logger.info(f"Existing watchlist columns: {existing_cols}")
        
        statements = []
        
        if 'notes' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN notes TEXT;')
        
        if 'last_job_id' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT;')
        
        if 'last_analyzed_at' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP;')
        
        if 'last_status' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_status TEXT;')
        
        migration_sql = '\n'.join(statements)
        
        if not migration_sql.strip():
            logger.info("Migration v2: No changes needed")
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (%s, %s)
            ''', (2, "Watchlist columns (already present)"))
            conn.commit()
            return True
        
        return apply_migration(conn, 2, "Add watchlist columns", migration_sql)
    
    except Exception as e:
        logger.error(f"✗ Migration v2 failed: {e}")
        conn.rollback()
        return False


def migration_v3(conn):
    """
    Migration V3: Add job tracking columns and indices
    """
    cursor = conn.cursor()
    try:
        logger.info("Running migration v3...")
        
        # Check for tickers_json column
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='analysis_jobs' AND column_name='tickers_json'
        """)
        
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
            logger.info("  ✓ Added tickers_json column")
        
        conn.commit()
        
        # Create indices
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_tickers
                ON analysis_jobs(tickers_json, status)
            ''')
            logger.info("  ✓ Created index on (tickers_json, status)")
        except Exception as e:
            logger.debug(f"  Index may already exist: {e}")
        
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                ON analysis_results(ticker, CAST(created_at AS DATE))
            ''')
            logger.info("  ✓ Created UNIQUE index on (ticker, date)")
        except Exception as e:
            logger.debug(f"  Index may already exist: {e}")
        
        conn.commit()
        
        logger.info("[OK] Migration v3 completed")
        return apply_migration(conn, 3, "Job tracking columns and indices", "")
        
    except Exception as e:
        logger.error(f"✗ Migration v3 failed: {e}")
        conn.rollback()
        return False


def migration_v4(conn):
    """
    Migration V4: Ensure watchlist.ticker is primary identifier
    
    PostgreSQL only - simply uses ALTER TABLE RENAME if needed.
    """
    cursor = conn.cursor()
    try:
        logger.info("Running migration v4: Ensure watchlist.ticker is primary key...")
        
        # Check current columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='watchlist'
            ORDER BY ordinal_position
        """)
        columns = {row[0] for row in cursor.fetchall()}
        logger.info(f"Current watchlist columns: {columns}")
        
        # Check if we need to rename symbol -> ticker
        if 'symbol' in columns and 'ticker' not in columns:
            logger.info("Renaming 'symbol' to 'ticker'...")
            cursor.execute("ALTER TABLE watchlist RENAME COLUMN symbol TO ticker")
            conn.commit()
            logger.info("✓ Column renamed successfully")
        
        # Check if we need to drop duplicate symbol column
        if 'ticker' in columns and 'symbol' in columns:
            logger.info("Dropping duplicate 'symbol' column...")
            cursor.execute("ALTER TABLE watchlist DROP COLUMN symbol")
            conn.commit()
            logger.info("✓ Duplicate column removed")
        
        logger.info("[OK] Migration v4 completed")
        return apply_migration(conn, 4, "Ensure watchlist.ticker exists", "")
        
    except Exception as e:
        logger.error(f"✗ Migration v4 failed: {e}")
        conn.rollback()
        return False


def migration_v5(conn):
    """
    Migration V5: Add analysis result tracking columns
    """
    cursor = conn.cursor()
    try:
        logger.info("Running migration v5...")
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='analysis_results'
        """)
        existing_cols = {row[0] for row in cursor.fetchall()}
        
        statements = []
        
        if 'job_id' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN job_id TEXT;')
        
        if 'started_at' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP;')
        
        if 'completed_at' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP;')
        
        migration_sql = '\n'.join(statements)
        
        if not migration_sql.strip():
            logger.info("Migration v5: No changes needed")
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (%s, %s)
            ''', (5, "Analysis result tracking (already present)"))
            conn.commit()
            return True
        
        return apply_migration(conn, 5, "Add analysis result tracking columns", migration_sql)
    
    except Exception as e:
        logger.error(f"✗ Migration v5 failed: {e}")
        conn.rollback()
        return False


def run_migrations():
    """
    Main entry point: Apply all pending migrations in sequence.
    
    Returns:
        bool: True if all migrations applied successfully, False otherwise
    """
    try:
        logger.info("=" * 70)
        logger.info("DATABASE MIGRATIONS - Starting migration sequence (PostgreSQL)")
        logger.info("=" * 70)
        
        # Get database connection
        conn = get_migration_conn()
        logger.info("✓ Connected to PostgreSQL database")
        
        # Initialize version tracking
        init_version_table(conn)
        current_version = get_current_version(conn)
        logger.info(f"Current schema version: {current_version}")
        logger.info(f"Target schema version: {CURRENT_SCHEMA_VERSION}")
        
        if current_version >= CURRENT_SCHEMA_VERSION:
            logger.info("✓ Database schema is up-to-date, no migrations needed")
            conn.close()
            return True
        
        # Apply migrations in sequence
        migrations = [
            (1, migration_v1),
            (2, migration_v2),
            (3, migration_v3),
            (4, migration_v4),
            (5, migration_v5),
        ]
        
        pending_count = sum(1 for v, _ in migrations if v > current_version)
        logger.info(f"\nApplying {pending_count} pending migrations...\n")
        
        for version, migration_func in migrations:
            if version <= current_version:
                logger.debug(f"Skipping v{version} (already applied)")
                continue
            
            logger.info(f"\n--- Migration v{version} ---")
            success = migration_func(conn)
            
            if not success:
                logger.error(f"✗ Migration v{version} FAILED - stopping")
                conn.close()
                return False
        
        # Verify final version
        final_version = get_current_version(conn)
        conn.close()
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✓ MIGRATIONS COMPLETE - Final schema version: {final_version}")
        logger.info("=" * 70)
        
        return final_version >= CURRENT_SCHEMA_VERSION
        
    except Exception as e:
        logger.error(f"✗ CRITICAL: Migration system failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s'
    )
    success = run_migrations()
    sys.exit(0 if success else 1)
