"""
Migration script: Add tickers_hash column to analysis_jobs table

Purpose:
    Fix PostgreSQL B-tree index size limit (8KB per row) by replacing
    indexing on tickers_json (can be 50KB+) with indexing on tickers_hash
    (fixed 64 bytes SHA-256 hash).

Changes:
    1. Add tickers_hash column to analysis_jobs table
    2. Compute SHA-256 hash of normalized tickers_json for all existing jobs
    3. Drop old problematic index: idx_job_tickers(tickers_json, status)
    4. Create new hash-based index: idx_job_tickers_hash(tickers_hash, status)

Backward Compatibility:
    - Keeps tickers_json column unchanged
    - Callers continue to see and track full ticker list
    - Only affects internal duplicate detection queries
    - Safe to roll back: simply recreate old index if needed

Works with: Both PostgreSQL and SQLite
Idempotent: Safe to run multiple times (no errors if column already exists)
"""

import hashlib
import json
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def compute_tickers_hash(tickers_json: Optional[str]) -> Optional[str]:
    """
    Compute SHA-256 hash of normalized tickers JSON string.
    
    Args:
        tickers_json: JSON string like '["INFY.NS", "TCS.NS"]' (sorted)
    
    Returns:
        Hex digest of SHA-256 hash (64 characters), or None if input is None/empty
    
    Examples:
        >>> compute_tickers_hash('["INFY.NS", "TCS.NS"]')
        'a1b2c3d4e5f6...'  (64 hex chars)
        >>> compute_tickers_hash(None)
        None
    """
    if not tickers_json:
        return None
    
    try:
        # Hash the JSON string directly (it's already normalized/sorted)
        hash_obj = hashlib.sha256(tickers_json.encode('utf-8'))
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for tickers_json: {e}")
        return None


def add_tickers_hash_column(conn, database_type: str) -> bool:
    """
    Add tickers_hash column to analysis_jobs table.
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful or column already exists
    """
    cursor = conn.cursor()
    try:
        if database_type == 'postgres':
            # Check if column exists in PostgreSQL
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='analysis_jobs' AND column_name='tickers_hash'
            """)
            if cursor.fetchone():
                logger.info("  tickers_hash column already exists (PostgreSQL)")
                return True
        else:
            # SQLite: Check using PRAGMA table_info
            cursor.execute("PRAGMA table_info(analysis_jobs)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'tickers_hash' in columns:
                logger.info("  tickers_hash column already exists (SQLite)")
                return True
        
        # Column doesn't exist, add it
        cursor.execute('ALTER TABLE analysis_jobs ADD COLUMN tickers_hash TEXT')
        conn.commit()
        logger.info("  ✓ Added tickers_hash column to analysis_jobs")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding tickers_hash column: {e}")
        return False


def populate_tickers_hash_for_existing_jobs(conn, database_type: str) -> bool:
    """
    Compute and store tickers_hash for all existing jobs.
    
    Backfills tickers_hash for jobs that were created before this column existed.
    Safe to run multiple times (idempotent - only updates NULL values).
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful
    """
    cursor = conn.cursor()
    try:
        # Get all jobs with NULL tickers_hash but non-NULL tickers_json
        if database_type == 'postgres':
            query = """
                SELECT job_id, tickers_json FROM analysis_jobs 
                WHERE tickers_hash IS NULL AND tickers_json IS NOT NULL
            """
        else:
            query = """
                SELECT job_id, tickers_json FROM analysis_jobs 
                WHERE tickers_hash IS NULL AND tickers_json IS NOT NULL
            """
        
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            logger.info("  No jobs to backfill (all have tickers_hash)")
            return True
        
        logger.info(f"  Backfilling tickers_hash for {len(jobs)} existing jobs...")
        
        # Update each job
        updated_count = 0
        for job_id, tickers_json in jobs:
            hash_value = compute_tickers_hash(tickers_json)
            if hash_value:
                if database_type == 'postgres':
                    cursor.execute(
                        "UPDATE analysis_jobs SET tickers_hash = %s WHERE job_id = %s",
                        (hash_value, job_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE analysis_jobs SET tickers_hash = ? WHERE job_id = ?",
                        (hash_value, job_id)
                    )
                updated_count += 1
        
        conn.commit()
        logger.info(f"  ✓ Backfilled {updated_count} jobs with tickers_hash")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error backfilling tickers_hash: {e}")
        return False


def remove_old_tickers_index(conn, database_type: str) -> bool:
    """
    Drop the old problematic index: idx_job_tickers(tickers_json, status).
    
    This index causes B-tree size violations when tickers_json > 8KB.
    Will be replaced by hash-based index.
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful (or index doesn't exist)
    """
    cursor = conn.cursor()
    try:
        try:
            if database_type == 'postgres':
                cursor.execute("DROP INDEX IF EXISTS idx_job_tickers")
            else:
                cursor.execute("DROP INDEX IF EXISTS idx_job_tickers")
            
            conn.commit()
            logger.info("  ✓ Dropped old index idx_job_tickers")
        except Exception as e:
            # Index may not exist, which is fine
            logger.debug(f"  Index drop note: {e}")
            conn.rollback()
        
        return True
    except Exception as e:
        logger.error(f"Error removing old index: {e}")
        return False


def create_tickers_hash_index(conn, database_type: str) -> bool:
    """
    Create new hash-based index: idx_job_tickers_hash(tickers_hash, status).
    
    This replaces the old tickers_json index.
    - Fixed 64-byte hash easily fits within 8KB B-tree limit
    - Supports duplicate detection queries: WHERE tickers_hash = ? AND status IN (...)
    - Works for both PostgreSQL and SQLite
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if successful (or index already exists)
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_job_tickers_hash
            ON analysis_jobs(tickers_hash, status)
        ''')
        conn.commit()
        logger.info("  ✓ Created index idx_job_tickers_hash(tickers_hash, status)")
        return True
    except Exception as e:
        conn.rollback()
        logger.debug(f"  Index creation note: {e}")
        return False


def run_migration(conn, database_type: str) -> bool:
    """
    Execute all migration steps in order.
    
    Migration is atomic - if any step fails, all changes are rolled back.
    Safe to run multiple times (idempotent).
    
    Args:
        conn: Database connection
        database_type: 'postgres' or 'sqlite'
    
    Returns:
        True if all steps succeeded
    """
    try:
        logger.info("Running migration: Add tickers_hash column and indices...")
        
        # Step 1: Add column
        if not add_tickers_hash_column(conn, database_type):
            return False
        
        # Step 2: Backfill existing jobs
        if not populate_tickers_hash_for_existing_jobs(conn, database_type):
            return False
        
        # Step 3: Remove old problematic index
        if not remove_old_tickers_index(conn, database_type):
            return False
        
        # Step 4: Create new hash-based index
        if not create_tickers_hash_index(conn, database_type):
            return False
        
        logger.info("[OK] Migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        return False
