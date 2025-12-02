#!/usr/bin/env python3
"""
Clear stale job state from in-memory cache.

This fixes the issue where bulk analysis progress shows inflated numbers
from previous runs. The in-memory cache persists across API calls and needs
to be cleared when starting fresh analysis.
"""

import sys
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from models.job_state import get_job_state_manager
from database import query_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_old_jobs_from_cache():
    """Clear old/completed jobs from job state manager"""
    job_state_manager = get_job_state_manager()
    
    logger.info("Current in-memory jobs:")
    all_jobs = job_state_manager.get_all_jobs()
    for job_id, state in all_jobs.items():
        logger.info(f"  {job_id[:12]}... | Status: {state.get('status')} | Total: {state.get('total')}")
    
    # Get active jobs from database (source of truth)
    try:
        active_db_jobs = query_db("""
            SELECT job_id FROM analysis_jobs 
            WHERE status IN ('queued', 'processing')
        """)
        active_job_ids = {row[0] for row in active_db_jobs} if active_db_jobs else set()
        logger.info(f"\nActive jobs in database: {active_job_ids}")
    except Exception as e:
        logger.error(f"Failed to query database: {e}")
        active_job_ids = set()
    
    # Remove jobs from memory that are not in database
    logger.info("\nCleaning up stale jobs from cache...")
    to_delete = []
    for job_id, state in all_jobs.items():
        status = state.get('status', 'unknown')
        # Delete if: (1) completed/failed job, or (2) not in active database jobs
        if status not in ('queued', 'processing') or job_id not in active_job_ids:
            to_delete.append((job_id, status))
            job_state_manager.delete_job(job_id)
            logger.info(f"  ✓ Deleted {job_id[:12]}... (status: {status})")
    
    if not to_delete:
        logger.info("  (No stale jobs to delete)")
    
    logger.info(f"\nCleanup complete! Deleted {len(to_delete)} jobs from cache")
    
    # Show remaining jobs
    remaining = job_state_manager.get_all_jobs()
    if remaining:
        logger.info(f"\nRemaining jobs in cache: {len(remaining)}")
        for job_id, state in remaining.items():
            logger.info(f"  {job_id[:12]}... | Status: {state.get('status')} | Total: {state.get('total')}")
    else:
        logger.info("\n✓ Cache is now empty (fresh start)")
    
    return len(to_delete)


def check_database_jobs():
    """Check what jobs are actually in the database"""
    logger.info("\n" + "="*80)
    logger.info("Database Jobs (Source of Truth):")
    logger.info("="*80)
    
    try:
        jobs = query_db("""
            SELECT job_id, status, total, completed, created_at
            FROM analysis_jobs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        if jobs:
            total_sum = 0
            for job_id, status, total, completed, created_at in jobs:
                logger.info(f"  {job_id[:12]}... | {status:12} | Total: {total:5} | Completed: {completed:5} | {created_at[:19]}")
                total_sum += total
            
            logger.info(f"\nTotal stocks across all jobs: {total_sum}")
            logger.info(f"Expected per run: 2192 stocks")
            if total_sum > 2192:
                logger.warning(f"⚠️  Sum ({total_sum}) is > 2192 - suggests multiple runs or duplication")
        else:
            logger.info("  (No jobs in database)")
    except Exception as e:
        logger.error(f"Failed to query jobs: {e}")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("JOB STATE CLEANUP TOOL")
    logger.info("=" * 80)
    
    check_database_jobs()
    
    logger.info("\n" + "="*80)
    logger.info("Cleaning in-memory job cache...")
    logger.info("="*80 + "\n")
    
    count = clear_old_jobs_from_cache()
    
    logger.info("\n" + "="*80)
    if count > 0:
        logger.info("✓ Cache cleanup complete")
        logger.info("You can now run 'Analyze All' again with a fresh start")
    else:
        logger.info("✓ Cache was already clean")
    logger.info("="*80)
