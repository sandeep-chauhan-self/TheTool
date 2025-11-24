"""
Migration script: Fix duplicate key constraint for re-analysis

Purpose:
    The UNIQUE index idx_analysis_ticker_date(ticker, date) prevents
    re-analyzing the same stock on the same day. This is too restrictive -
    users should be able to re-run "Analyze All Stocks" multiple times
    without duplicate key violations.

Solution:
    - Drop the UNIQUE constraint
    - Keep regular indices for query performance
    - Allow multiple analyses per stock per day

Works with: Both PostgreSQL and SQLite
Idempotent: Safe to run multiple times
"""

import logging

logger = logging.getLogger(__name__)


def drop_unique_ticker_date_index(conn, database_type: str) -> bool:
    """
    Drop the UNIQUE index that prevents re-analysis on the same day.
    
    This allows users to re-run "Analyze All Stocks" without hitting
    duplicate key violations.
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful (or index doesn't exist)
    """
    cursor = conn.cursor()
    try:
        # Drop the problematic UNIQUE index
        try:
            cursor.execute("DROP INDEX IF EXISTS idx_analysis_ticker_date")
            conn.commit()
            logger.info("  ✓ Dropped UNIQUE index idx_analysis_ticker_date")
        except Exception as e:
            # Index may not exist, which is fine
            logger.debug(f"  Index drop note: {e}")
            conn.rollback()
        
        return True
    except Exception as e:
        logger.error(f"Error removing UNIQUE index: {e}")
        return False


def create_regular_indices(conn, database_type: str) -> bool:
    """
    Create regular (non-unique) indices for query performance.
    
    These indices help with queries but don't prevent duplicates,
    allowing multiple analyses per stock per day.
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful (or indices already exist)
    """
    cursor = conn.cursor()
    try:
        # Create regular indices for performance
        # Index 1: ticker, created_at for filtering by date range
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_ticker_created
                ON analysis_results(ticker, created_at DESC)
            ''')
            logger.info("  ✓ Created index on (ticker, created_at)")
        except Exception as e:
            logger.debug(f"  Index may already exist: {e}")
        
        # Index 2: created_at for time-based queries
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_created_date
                ON analysis_results(CAST(created_at AS DATE) DESC)
            ''')
            logger.info("  ✓ Created index on (created_at date)")
        except Exception as e:
            logger.debug(f"  Index may already exist: {e}")
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating indices: {e}")
        conn.rollback()
        return False


def run_migration(conn, database_type: str) -> bool:
    """
    Execute all migration steps in order.
    
    Removes the restrictive UNIQUE constraint and replaces it with
    regular indices for better query performance without duplicate
    key violations.
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if all steps succeeded
    """
    try:
        logger.info("Running migration: Fix duplicate key constraint for re-analysis...")
        
        # Step 1: Drop the problematic UNIQUE index
        if not drop_unique_ticker_date_index(conn, database_type):
            return False
        
        # Step 2: Create regular indices for performance
        if not create_regular_indices(conn, database_type):
            return False
        
        logger.info("[OK] Migration completed successfully - re-analysis now allowed")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
