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
        # PostgreSQL: execute statements individually
        if migration_sql.strip():
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            logger.info(f"  Executing {len(statements)} SQL statement(s)...")
            for i, stmt in enumerate(statements, 1):
                if stmt:
                    logger.info(f"    [{i}/{len(statements)}] Running SQL...")
                    cursor.execute(stmt)
            logger.info(f"  ✓ SQL complete")
        
        # Record migration using PostgreSQL format
        logger.info(f"  Recording in db_version...")
        cursor.execute('''
            INSERT INTO db_version (version, description)
            VALUES (%s, %s)
        ''', (version, description))
        
        conn.commit()
        logger.info(f"  ✓ v{version} applied successfully")
        return True
    except Exception as e:
        logger.error(f"  ✗ v{version} failed: {e}", exc_info=True)
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
        logger.info("  Checking watchlist table columns...")
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'watchlist'
        """)
        existing_cols = {row[0] for row in cursor.fetchall()}
        logger.info(f"  Found {len(existing_cols)} columns")
        
        statements = []
        to_add = []
        
        if 'notes' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN notes TEXT;')
            to_add.append('notes')
        
        if 'last_job_id' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT;')
            to_add.append('last_job_id')
        
        if 'last_analyzed_at' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP;')
            to_add.append('last_analyzed_at')
        
        if 'last_status' not in existing_cols:
            statements.append('ALTER TABLE watchlist ADD COLUMN last_status TEXT;')
            to_add.append('last_status')
        
        migration_sql = '\n'.join(statements)
        
        if not migration_sql.strip():
            logger.info("  ✓ All columns already present")
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (%s, %s)
            ''', (2, "Watchlist columns (already present)"))
            conn.commit()
            logger.info("  ✓ v2 recorded (no-op)")
            return True
        
        logger.info(f"  Need to add: {', '.join(to_add)}")
        return apply_migration(conn, 2, "Add watchlist columns", migration_sql)
    
    except Exception as e:
        logger.error(f"  ✗ v2 failed: {e}", exc_info=True)
        conn.rollback()
        return False


def migration_v3(conn):
    """
    Migration V3: Add job tracking columns and indices
    """
    cursor = conn.cursor()
    try:
        logger.info("  Checking analysis_jobs table...")
        
        # Check for tickers_json column
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='analysis_jobs' AND column_name='tickers_json'
        """)
        
        if not cursor.fetchone():
            logger.info("    Column missing, adding tickers_json...")
            cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_json TEXT')
            logger.info("  ✓ Added tickers_json column")
        else:
            logger.info("  Column already exists")
        
        conn.commit()
        
        # Create indices
        logger.info("  Creating indices...")
        try:
            logger.info("    Creating idx_job_tickers...")
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_tickers
                ON analysis_jobs(tickers_json, status)
            ''')
            logger.info("      ✓ Created")
        except Exception as e:
            logger.info(f"      (Already exists)")
        
        try:
            logger.info("    Creating idx_analysis_ticker_date...")
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                ON analysis_results(ticker, CAST(created_at AS DATE))
            ''')
            logger.info("      ✓ Created")
        except Exception as e:
            logger.info(f"      (Already exists)")
        
        conn.commit()
        
        logger.info("  ✓ Indices complete")
        return apply_migration(conn, 3, "Job tracking columns and indices", "")
        
    except Exception as e:
        logger.error(f"  ✗ v3 failed: {e}", exc_info=True)
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
        logger.info(f"  Found {len(columns)} columns")
        
        # Check if we need to rename symbol -> ticker
        if 'symbol' in columns and 'ticker' not in columns:
            logger.info("  Renaming 'symbol' → 'ticker'...")
            cursor.execute("ALTER TABLE watchlist RENAME COLUMN symbol TO ticker")
            conn.commit()
            logger.info("  ✓ Renamed")
        elif 'ticker' in columns:
            logger.info("  ✓ 'ticker' present")
        
        # Check if we need to drop duplicate symbol column
        if 'ticker' in columns and 'symbol' in columns:
            logger.info("  Dropping duplicate 'symbol'...")
            cursor.execute("ALTER TABLE watchlist DROP COLUMN symbol")
            conn.commit()
            logger.info("  ✓ Removed")
        
        return apply_migration(conn, 4, "Ensure watchlist.ticker exists", "")
        
    except Exception as e:
        logger.error(f"  ✗ v4 failed: {e}", exc_info=True)
        conn.rollback()
        return False


def migration_v5(conn):
    """
    Migration V5: Add analysis result tracking columns
    """
    cursor = conn.cursor()
    try:
        logger.info("  Checking analysis_results table columns...")
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='analysis_results'
        """)
        existing_cols = {row[0] for row in cursor.fetchall()}
        logger.info(f"  Found {len(existing_cols)} columns")
        
        statements = []
        to_add = []
        
        if 'job_id' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN job_id TEXT;')
            to_add.append('job_id')
        
        if 'started_at' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP;')
            to_add.append('started_at')
        
        if 'completed_at' not in existing_cols:
            statements.append('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP;')
            to_add.append('completed_at')
        
        migration_sql = '\n'.join(statements)
        
        if not migration_sql.strip():
            logger.info("  ✓ All columns already present")
            cursor.execute('''
                INSERT INTO db_version (version, description)
                VALUES (%s, %s)
            ''', (5, "Analysis result tracking (already present)"))
            conn.commit()
            logger.info("  ✓ v5 recorded (no-op)")
            return True
        
        logger.info(f"  Adding {len(to_add)} columns: {', '.join(to_add)}")
        return apply_migration(conn, 5, "Add analysis result tracking columns", migration_sql)
    
    except Exception as e:
        logger.error(f"  ✗ v5 failed: {e}", exc_info=True)
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
        logger.info("Connecting to PostgreSQL...")
        conn = get_migration_conn()
        logger.info("✓ Connected")
        
        # Initialize version tracking
        logger.info("Initializing version tracking...")
        init_version_table(conn)
        current_version = get_current_version(conn)
        logger.info(f"Current schema version:  v{current_version}")
        logger.info(f"Target schema version:   v{CURRENT_SCHEMA_VERSION}")
        
        if current_version >= CURRENT_SCHEMA_VERSION:
            logger.info("✓ Schema is current - no migrations needed")
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
        logger.info(f"")
        logger.info(f"Pending migrations: {pending_count}")
        if pending_count > 0:
            logger.info(f"  v{current_version + 1} → v{CURRENT_SCHEMA_VERSION}")
        logger.info(f"")
        
        for version, migration_func in migrations:
            if version <= current_version:
                logger.info(f"  [v{version}] Already applied")
                continue
            
            logger.info(f"")
            logger.info(f"▶ Executing Migration v{version}...")
            success = migration_func(conn)
            
            if not success:
                logger.error(f"")
                logger.error(f"✗ Migration v{version} FAILED - aborting")
                logger.error(f"")
                conn.close()
                return False
        
        # Verify final version
        logger.info(f"")
        logger.info(f"Verifying final schema version...")
        final_version = get_current_version(conn)
        conn.close()
        
        logger.info(f"")
        logger.info("=" * 70)
        if final_version >= CURRENT_SCHEMA_VERSION:
            logger.info(f"✓ MIGRATIONS COMPLETE")
            logger.info(f"  Final schema version: v{final_version}")
        else:
            logger.error(f"⚠ INCOMPLETE: v{final_version} (expected v{CURRENT_SCHEMA_VERSION})")
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
