#!/usr/bin/env python3
"""
Scheduled Cleanup Script for Analysis Jobs and Results

This script is executed daily by GitHub Actions to:
1. Remove analysis jobs older than 7 days
2. Deduplicate analysis results (keep only the latest per job_id and ticker)

Usage:
    python cleanup_old_jobs.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
    CLEANUP_DAYS: Days to keep analysis jobs (default: 7)
    PYTHONPATH: Should include 'backend' for module imports

Exit Codes:
    0: Success
    1: Failure (database error, configuration error, etc.)
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone

# Setup logging to both console and file
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'cleanup.log')

# Configure logging format
log_format = '%(asctime)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))

file_handler = logging.FileHandler(LOG_FILE, mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format, date_format))

# Configure root logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_database_url():
    """Get and validate DATABASE_URL from environment."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set")
        return None
    
    # Fix PostgreSQL URL format (Railway may use postgres:// instead of postgresql://)
    if database_url.startswith('postgres://'):
        database_url = 'postgresql://' + database_url[11:]
    
    return database_url


def cleanup_old_jobs(cursor, days=7):
    """
    Delete analysis jobs older than the specified number of days.
    
    Args:
        cursor: Database cursor
        days: Number of days to keep (default: 7)
    
    Returns:
        int: Number of deleted rows
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"Deleting analysis_jobs older than {days} days (before {cutoff_str})")
    
    cursor.execute(
        "DELETE FROM analysis_jobs WHERE created_at < %s",
        (cutoff_str,)
    )
    
    deleted_count = cursor.rowcount
    logger.info(f"Deleted {deleted_count} old analysis jobs")
    
    return deleted_count


def deduplicate_results(cursor):
    """
    Remove duplicate analysis results, keeping only the latest per job_id and ticker.
    
    For results without a job_id, keeps only the latest per ticker.
    
    Args:
        cursor: Database cursor
    
    Returns:
        int: Number of deleted duplicate rows
    """
    logger.info("Deduplicating analysis_results (keeping latest per job_id and ticker)")
    
    # Delete duplicates: keep only the row with the highest id for each (job_id, ticker) combination
    # This handles both cases: results with job_id and results without (using ticker only)
    cursor.execute("""
        DELETE FROM analysis_results
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM analysis_results
            GROUP BY COALESCE(job_id, ''), ticker
        )
    """)
    
    deleted_count = cursor.rowcount
    logger.info(f"Deleted {deleted_count} duplicate analysis results")
    
    return deleted_count


def check_job_id_column(cursor):
    """
    Check if job_id column exists in analysis_results table.
    
    Args:
        cursor: Database cursor
    
    Returns:
        bool: True if job_id column exists, False otherwise
    """
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'analysis_results' AND column_name = 'job_id'
    """)
    return cursor.fetchone() is not None


def deduplicate_results_without_job_id(cursor):
    """
    Remove duplicate analysis results when job_id column doesn't exist.
    Keeps only the latest per ticker.
    
    Args:
        cursor: Database cursor
    
    Returns:
        int: Number of deleted duplicate rows
    """
    logger.info("Deduplicating analysis_results by ticker only (no job_id column)")
    
    cursor.execute("""
        DELETE FROM analysis_results
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM analysis_results
            GROUP BY ticker
        )
    """)
    
    deleted_count = cursor.rowcount
    logger.info(f"Deleted {deleted_count} duplicate analysis results")
    
    return deleted_count


def run_cleanup():
    """
    Main cleanup function. Connects to database and runs cleanup operations.
    
    Returns:
        bool: True on success, False on failure
    """
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 module not installed. Install with: pip install psycopg2-binary")
        return False
    
    database_url = get_database_url()
    if not database_url:
        return False
    
    conn = None
    cursor = None
    
    try:
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        logger.info("Database connection established")
        
        # Get cleanup configuration
        cleanup_days = int(os.environ.get('CLEANUP_DAYS', '7'))
        
        # Run cleanup operations
        jobs_deleted = cleanup_old_jobs(cursor, days=cleanup_days)
        
        # Check if job_id column exists and use appropriate deduplication
        has_job_id = check_job_id_column(cursor)
        if has_job_id:
            results_deleted = deduplicate_results(cursor)
        else:
            results_deleted = deduplicate_results_without_job_id(cursor)
        
        # Commit changes
        conn.commit()
        logger.info("Cleanup completed successfully")
        logger.info(f"Summary: {jobs_deleted} jobs deleted, {results_deleted} duplicate results removed")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            try:
                conn.rollback()
                logger.info("Transaction rolled back")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if conn:
            try:
                conn.rollback()
                logger.info("Transaction rolled back")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
        return False
        
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
                logger.info("Database connection closed")
            except Exception:
                pass


def main():
    """Entry point for the cleanup script."""
    logger.info("=" * 60)
    logger.info("Starting scheduled cleanup job")
    logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)
    
    success = run_cleanup()
    
    logger.info("=" * 60)
    if success:
        logger.info("Cleanup job completed successfully")
        sys.exit(0)
    else:
        logger.error("Cleanup job failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
