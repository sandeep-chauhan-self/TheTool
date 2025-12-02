#!/usr/bin/env python3
"""Remove indexes from analysis_jobs table to align with development decision"""
import sqlite3
from config import config

def fix_indexes():
    db_path = config.DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop all indexes from analysis_jobs
    indexes_to_drop = [
        'idx_job_status',
        'idx_job_tickers_hash',
        'idx_job_tickers',
        'idx_jobs_status'
    ]
    
    for idx in indexes_to_drop:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {idx}")
            print(f"✓ Dropped index: {idx}")
        except Exception as e:
            print(f"✗ Failed to drop {idx}: {e}")
    
    conn.commit()
    
    # Verify remaining indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='analysis_jobs'")
    remaining = [row[0] for row in cursor.fetchall()]
    
    print(f"\nRemaining indexes on analysis_jobs: {remaining if remaining else 'None (correct!)'}")
    conn.close()
    
    return len(remaining) == 0

if __name__ == '__main__':
    if fix_indexes():
        print("\n✅ Database indexes fixed successfully!")
    else:
        print("\n⚠️ Some indexes remain - this may be expected")
