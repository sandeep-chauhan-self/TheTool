#!/usr/bin/env python3
"""Verify the database fix - ensure tickers_json column exists and schema is correct"""
import sqlite3
import json
from config import config

def verify_schema():
    db_path = config.DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("SCHEMA VERIFICATION: analysis_jobs TABLE")
    print("=" * 60)
    
    # Check columns
    cursor.execute("PRAGMA table_info(analysis_jobs)")
    columns = cursor.fetchall()
    
    print("\n✓ Columns in analysis_jobs:")
    column_names = []
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        column_names.append(col_name)
        print(f"  - {col_name}: {col_type}")
    
    # Check for tickers_json column
    if 'tickers_json' in column_names:
        print("\n✅ tickers_json column EXISTS - GOOD!")
    else:
        print("\n❌ tickers_json column MISSING - PROBLEM!")
        conn.close()
        return False
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='analysis_jobs'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    print(f"\n✓ Indexes on analysis_jobs:")
    if indexes:
        for idx in indexes:
            print(f"  - {idx}")
    else:
        print("  (None - table scan will be used)")
    
    # Test INSERT with tickers_json
    print("\n" + "=" * 60)
    print("TEST: INSERT with tickers_json column")
    print("=" * 60)
    
    try:
        test_tickers = json.dumps(['RELIANCE.NS', 'TCS.NS'])
        cursor.execute("""
            INSERT INTO analysis_jobs 
            (job_id, status, progress, total, completed, successful, errors, tickers_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, ('test-job-123', 'pending', 0, 2, 0, 0, '[]', test_tickers))
        
        conn.commit()
        print("✅ INSERT succeeded!")
        
        # Verify the insert
        cursor.execute("SELECT job_id, tickers_json FROM analysis_jobs WHERE job_id = ?", ('test-job-123',))
        row = cursor.fetchone()
        if row:
            print(f"\n✓ Retrieved: job_id={row[0]}, tickers_json={row[1]}")
            
            # Clean up test data
            cursor.execute("DELETE FROM analysis_jobs WHERE job_id = ?", ('test-job-123',))
            conn.commit()
            print("✓ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test INSERT failed: {e}")
        conn.close()
        return False
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE - Database is ready!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    verify_schema()
