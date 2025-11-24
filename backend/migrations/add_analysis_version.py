"""
Migration v6: Add Analysis Versioning

Purpose:
  - Track multiple analysis iterations per stock
  - Enable historical data retention
  - Support re-analysis without losing previous data
  - Provide version tracking for audit trail

Changes:
  1. Add 'analysis_version' column to analysis_results
  2. Create index on (ticker, analysis_version DESC) for efficient queries
  3. Backfill all existing data with version = 0
  4. Add version column to watchlist (optional for future history)

Reversibility:
  - Can be rolled back by dropping column if needed
  - Existing data stays intact (default value 0)
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def migration_v6_sqlite(connection: sqlite3.Connection) -> bool:
    """
    SQLite migration for analysis versioning.
    
    Args:
        connection: SQLite database connection
        
    Returns:
        True if successful, False if migration already applied or failed
    """
    cursor = connection.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(analysis_results)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'analysis_version' in columns:
            logger.info("✓ Migration v6: analysis_version column already exists (SQLite)")
            return True
        
        logger.info("Starting Migration v6: Adding analysis_version column (SQLite)...")
        
        # Step 1: Add analysis_version column with default 0
        cursor.execute("""
            ALTER TABLE analysis_results 
            ADD COLUMN analysis_version INTEGER DEFAULT 0
        """)
        logger.info("  ✓ Added analysis_version column to analysis_results")
        
        # Step 2: Create index for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_ticker_version 
            ON analysis_results(ticker, analysis_version DESC)
        """)
        logger.info("  ✓ Created index: idx_analysis_ticker_version")
        
        # Step 3: Backfill existing data with version 0
        # (Already done via DEFAULT 0, but explicit for clarity)
        cursor.execute("""
            UPDATE analysis_results 
            SET analysis_version = 0 
            WHERE analysis_version IS NULL
        """)
        count = cursor.rowcount
        logger.info(f"  ✓ Backfilled {count} rows with analysis_version = 0")
        
        # Optional: Add watchlist version tracking
        cursor.execute("PRAGMA table_info(watchlist)")
        watchlist_columns = {row[1] for row in cursor.fetchall()}
        
        if 'watchlist' in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'"
        ).fetchall()[0] if cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'"
        ).fetchall() else False:
            if 'latest_analysis_version' not in watchlist_columns:
                cursor.execute("""
                    ALTER TABLE watchlist 
                    ADD COLUMN latest_analysis_version INTEGER DEFAULT 0
                """)
                logger.info("  ✓ Added latest_analysis_version column to watchlist")
        
        connection.commit()
        logger.info("✓ Migration v6 completed successfully (SQLite)")
        return True
        
    except Exception as e:
        connection.rollback()
        logger.error(f"✗ Migration v6 failed (SQLite): {str(e)}")
        raise


def migration_v6_postgres(connection) -> bool:
    """
    PostgreSQL migration for analysis versioning.
    
    Args:
        connection: PostgreSQL database connection
        
    Returns:
        True if successful, False if migration already applied or failed
    """
    cursor = connection.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'analysis_results' 
            AND column_name = 'analysis_version'
        """)
        
        if cursor.fetchone():
            logger.info("✓ Migration v6: analysis_version column already exists (PostgreSQL)")
            return True
        
        logger.info("Starting Migration v6: Adding analysis_version column (PostgreSQL)...")
        
        # Step 1: Add analysis_version column with default 0
        cursor.execute("""
            ALTER TABLE analysis_results 
            ADD COLUMN analysis_version INTEGER DEFAULT 0
        """)
        logger.info("  ✓ Added analysis_version column to analysis_results")
        
        # Step 2: Create index for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_ticker_version 
            ON analysis_results(ticker, analysis_version DESC)
        """)
        logger.info("  ✓ Created index: idx_analysis_ticker_version")
        
        # Step 3: Backfill existing data with version 0
        cursor.execute("""
            UPDATE analysis_results 
            SET analysis_version = 0 
            WHERE analysis_version IS NULL
        """)
        count = cursor.rowcount
        logger.info(f"  ✓ Backfilled {count} rows with analysis_version = 0")
        
        # Optional: Add watchlist version tracking
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'watchlist' 
            AND column_name = 'latest_analysis_version'
        """)
        
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE watchlist 
                ADD COLUMN latest_analysis_version INTEGER DEFAULT 0
            """)
            logger.info("  ✓ Added latest_analysis_version column to watchlist")
        
        connection.commit()
        logger.info("✓ Migration v6 completed successfully (PostgreSQL)")
        return True
        
    except Exception as e:
        connection.rollback()
        logger.error(f"✗ Migration v6 failed (PostgreSQL): {str(e)}")
        raise


def rollback_v6_sqlite(connection: sqlite3.Connection) -> bool:
    """
    Rollback migration v6 for SQLite (remove version column).
    
    Args:
        connection: SQLite database connection
        
    Returns:
        True if successful
    """
    cursor = connection.cursor()
    
    try:
        logger.info("Rolling back Migration v6 (SQLite)...")
        
        # SQLite doesn't support DROP COLUMN directly in all versions
        # Use workaround: recreate table without the column
        cursor.execute("""
            CREATE TABLE analysis_results_backup AS 
            SELECT * EXCEPT (analysis_version, latest_analysis_version) 
            FROM analysis_results
        """)
        
        cursor.execute("DROP TABLE analysis_results")
        cursor.execute("ALTER TABLE analysis_results_backup RENAME TO analysis_results")
        
        connection.commit()
        logger.info("✓ Rollback completed (SQLite)")
        return True
        
    except Exception as e:
        connection.rollback()
        logger.error(f"✗ Rollback failed (SQLite): {str(e)}")
        raise


def rollback_v6_postgres(connection) -> bool:
    """
    Rollback migration v6 for PostgreSQL (remove version column).
    
    Args:
        connection: PostgreSQL database connection
        
    Returns:
        True if successful
    """
    cursor = connection.cursor()
    
    try:
        logger.info("Rolling back Migration v6 (PostgreSQL)...")
        
        # Drop indices first
        cursor.execute("""
            DROP INDEX IF EXISTS idx_analysis_ticker_version
        """)
        logger.info("  ✓ Dropped index: idx_analysis_ticker_version")
        
        # Drop column
        cursor.execute("""
            ALTER TABLE analysis_results 
            DROP COLUMN IF EXISTS analysis_version
        """)
        logger.info("  ✓ Dropped analysis_version column")
        
        cursor.execute("""
            ALTER TABLE watchlist 
            DROP COLUMN IF EXISTS latest_analysis_version
        """)
        logger.info("  ✓ Dropped latest_analysis_version column")
        
        connection.commit()
        logger.info("✓ Rollback completed (PostgreSQL)")
        return True
        
    except Exception as e:
        connection.rollback()
        logger.error(f"✗ Rollback failed (PostgreSQL): {str(e)}")
        raise
