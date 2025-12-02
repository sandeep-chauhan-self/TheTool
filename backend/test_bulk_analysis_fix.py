#!/usr/bin/env python3
"""
Test script to simulate the bulk analysis job that was failing with placeholder errors
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

# Remove old database for clean test
db_path = './data/trading_app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"[INFO] Removed old database at {db_path}")

from database import get_db_connection, init_db, _detect_connection_type
from db_migrations import run_migrations
from thread_tasks import _safe_execute

def test_bulk_analysis_inserts():
    """Simulate bulk analysis inserts that were failing"""
    print("\n" + "=" * 60)
    print("TESTING BULK ANALYSIS DATABASE INSERTS")
    print("=" * 60)
    
    # Initialize database
    print("\n[1] Initializing database...")
    init_db()
    print("[OK] Database initialized")
    
    # Run migrations to add job_id, started_at, completed_at columns
    print("\n[1b] Running database migrations...")
    run_migrations()
    print("[OK] Migrations completed")
    
    # Run migrations
    print("\n[1.5] Running database migrations...")
    run_migrations()
    print("[OK] Migrations completed")
    
    # Get connection
    print("\n[2] Getting database connection...")
    conn = get_db_connection()
    cursor = conn.cursor()
    actual_type = _detect_connection_type(conn)
    print(f"[OK] Connection type: {actual_type}")
    
    # Create a mock job
    job_id = "test-job-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\n[3] Creating test job: {job_id}")
    
    query = '''
        INSERT INTO analysis_jobs (job_id, status, total, created_at)
        VALUES (?, ?, ?, ?)
    '''
    _safe_execute(cursor, query, (job_id, 'processing', 5, datetime.now().isoformat()), conn)
    conn.commit()
    print("[OK] Job created")
    
    # Insert analysis results (this was failing with "near '%'" error)
    print("\n[4] Testing analysis result inserts (the failing scenario)...")
    
    test_data = [
        ('63MOONS.NS', 63.5, 'BUY', 100.0, 95.0, 110.0),
        ('A2ZINFRA.NS', -19.9, 'HOLD', 50.0, 45.0, 60.0),
        ('AAATECH.NS', 17.3, 'HOLD', 200.0, 190.0, 220.0),
        ('AADHARHFC.NS', -5.4, 'HOLD', 2500.0, 2400.0, 2700.0),
        ('AAKASH.NS', -14.2, 'HOLD', 44.0, 40.0, 50.0),
    ]
    
    for ticker, score, verdict, entry, stop_loss, target in test_data:
        raw_data = json.dumps([
            {'name': 'RSI', 'value': score},
            {'name': 'MACD', 'value': score * 0.5}
        ])
        
        query = '''
            INSERT INTO analysis_results 
            (job_id, ticker, score, verdict, entry, stop_loss, target, entry_method, data_source, is_demo_data, raw_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        try:
            _safe_execute(cursor, query, (
                job_id,
                ticker,
                score,
                verdict,
                entry,
                stop_loss,
                target,
                'Market Order',
                'real',
                0,
                raw_data,
                datetime.now().isoformat()
            ), conn)
            conn.commit()
            print(f"  [OK] Inserted {ticker}: score={score}, verdict={verdict}")
        except Exception as e:
            print(f"  [FAIL] Failed to insert {ticker}: {e}")
            conn.rollback()
            raise
    
    # Update progress (this was also failing)
    print("\n[5] Testing progress update (also was failing)...")
    
    query = '''
        UPDATE analysis_jobs 
        SET progress = ?, completed = ?, successful = ?, errors = ?
        WHERE job_id = ?
    '''
    
    try:
        errors_json = json.dumps([])
        _safe_execute(cursor, query, (100, 5, 5, errors_json, job_id), conn)
        conn.commit()
        print("[OK] Progress updated successfully")
    except Exception as e:
        print(f"[FAIL] Failed to update progress: {e}")
        conn.rollback()
        raise
    
    # Mark job as completed
    print("\n[6] Marking job as completed...")
    query = '''
        UPDATE analysis_jobs 
        SET status = ?, completed_at = ?, errors = ?
        WHERE job_id = ?
    '''
    
    try:
        _safe_execute(cursor, query, ('completed', datetime.now().isoformat(), json.dumps([]), job_id), conn)
        conn.commit()
        print("[OK] Job marked as completed")
    except Exception as e:
        print(f"[FAIL] Failed to mark job completed: {e}")
        conn.rollback()
        raise
    
    # Verify data
    print("\n[7] Verifying data was inserted correctly...")
    cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE job_id = ?", (job_id,))
    count = cursor.fetchone()[0]
    print(f"[OK] Found {count} analysis results for job {job_id}")
    
    cursor.execute("SELECT ticker, score, verdict FROM analysis_results WHERE job_id = ? ORDER BY ticker", (job_id,))
    results = cursor.fetchall()
    for ticker, score, verdict in results:
        print(f"  - {ticker}: score={score}, verdict={verdict}")
    
    cursor.execute("SELECT status, progress FROM analysis_jobs WHERE job_id = ?", (job_id,))
    status, progress = cursor.fetchone()
    print(f"\n[OK] Job status: {status}, progress: {progress}%")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("[OK] BULK ANALYSIS TEST PASSED - NO PLACEHOLDER ERRORS")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        success = test_bulk_analysis_inserts()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
