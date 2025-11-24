#!/usr/bin/env python3
"""Quick test to verify tickers_json column exists and queries work"""
import sys
import json
sys.path.insert(0, '/c/Users/scst1/2025/TheTool/backend')

try:
    from database import query_db, get_db_session
    print("✓ Imports successful")
    
    # Test 1: Try to query analysis_jobs
    print("\nTest 1: Query analysis_jobs table...")
    try:
        result = query_db("SELECT COUNT(*) FROM analysis_jobs")
        print(f"✓ Successfully queried analysis_jobs: {result} rows")
    except Exception as e:
        print(f"✗ Failed to query: {e}")
        sys.exit(1)
    
    # Test 2: Query with tickers_json
    print("\nTest 2: Query with tickers_json column...")
    try:
        # This will fail if column doesn't exist
        result = query_db("""
            SELECT job_id, tickers_json FROM analysis_jobs 
            WHERE tickers_json IS NOT NULL LIMIT 1
        """)
        print(f"✓ Successfully queried tickers_json: {len(result)} rows")
    except Exception as e:
        print(f"✗ Failed to query tickers_json: {e}")
        sys.exit(1)
    
    print("\n✓ ALL TESTS PASSED - tickers_json column is accessible")
    
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
