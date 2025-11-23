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

DB_PATH = config.DB_PATH
CURRENT_SCHEMA_VERSION = 2


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
    """Apply a single migration"""
    cursor = conn.cursor()
    try:
        logger.info(f"Applying migration v{version}: {description}")
        cursor.executescript(migration_sql)
        cursor.execute('''
            INSERT INTO db_version (version, description)
            VALUES (?, ?)
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
    
    Adds:
    - ticker column (copy from symbol for existing rows)
    - notes column (for user annotations)
    
    This migration ensures backward compatibility with routes expecting ticker field.
    """
    migration_sql = '''
    -- Add ticker column if it doesn't exist
    ALTER TABLE watchlist ADD COLUMN ticker TEXT;
    
    -- Add notes column if it doesn't exist
    ALTER TABLE watchlist ADD COLUMN notes TEXT;
    
    -- Copy symbol to ticker for existing rows
    UPDATE watchlist SET ticker = symbol WHERE ticker IS NULL;
    '''
    
    return apply_migration(conn, 2, "Add ticker and notes to watchlist", migration_sql)


def run_migrations():
    """
    Run all pending migrations
    
    This is the main entry point. Call on app startup to ensure schema is current.
    Safe to call multiple times (idempotent).
    """
    import os
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
