"""
Backend Test Script - Verify All Components
"""

import sys
import os
import json
from pathlib import Path

# Ensure backend module can be imported regardless of working directory
# Add backend directory to sys.path if not already present
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import get_db_connection, init_db
from config import config

def get_table_columns(cursor, table_name):
    """
    Get table columns in a database-agnostic way.
    Returns a set of column names.
    """
    try:
        if config.DATABASE_TYPE == 'postgres':
            # PostgreSQL: Query information_schema
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = {row[0] for row in cursor.fetchall()}
        else:
            # SQLite: Use PRAGMA
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {row[1] for row in cursor.fetchall()}
        
        return columns
    except Exception as e:
        print(f"  [ERROR] Failed to get columns for {table_name}: {e}")
        return set()

print("=" * 60)
print("BACKEND COMPONENT TEST")
print("=" * 60)

# Test 1: Database Tables
print("\n[Test 1] Checking Database Tables...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if config.DATABASE_TYPE == 'postgres':
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables = [row[0] for row in cursor.fetchall()]
    else:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['watchlist', 'analysis_results', 'analysis_jobs', 'all_stocks_analysis']
    missing = [t for t in required_tables if t not in tables]
    
    if missing:
        print(f"  [FAIL] Missing tables: {missing}")
    else:
        print(f"  [PASS] All required tables exist: {required_tables}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 2: Check all_stocks_analysis structure
print("\n[Test 2] Checking all_stocks_analysis Table Structure...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    columns = get_table_columns(cursor, 'all_stocks_analysis')
    
    required_columns = {'id', 'symbol', 'name', 'yahoo_symbol', 'status', 'score', 'verdict', 
                       'entry', 'stop_loss', 'target', 'created_at', 'updated_at'}
    missing_cols = required_columns - columns
    
    if missing_cols:
        print(f"  [FAIL] Missing columns: {missing_cols}")
    else:
        print(f"  [PASS] All required columns exist")
    
    print(f"  Total columns: {len(columns)}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 3: Check watchlist user_id column
print("\n[Test 3] Checking watchlist Table for user_id...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    columns = get_table_columns(cursor, 'watchlist')
    
    if 'user_id' in columns:
        print(f"  [PASS] user_id column exists")
    else:
        print(f"  [FAIL] user_id column missing")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 4: Check NSE stocks data file
print("\n[Test 4] Checking NSE Stocks Data File...")
try:
    nse_path = os.path.join(os.getenv('DATA_PATH', './data'), 'nse_stocks.json')
    
    if os.path.exists(nse_path):
        with open(nse_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stock_count = len(data.get('stocks', []))
        print(f"  [PASS] File exists with {stock_count} stocks")
        
        if stock_count > 0:
            sample = data['stocks'][0]
            print(f"  Sample stock: {sample.get('symbol')} - {sample.get('name')}")
    else:
        print(f"  [FAIL] NSE stocks file not found at {nse_path}")
        
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 5: Check all_stocks_analysis record count
print("\n[Test 5] Checking all_stocks_analysis Records...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM all_stocks_analysis")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM all_stocks_analysis")
    unique_stocks = cursor.fetchone()[0]
    
    print(f"  Total records: {total_records}")
    print(f"  Unique stocks: {unique_stocks}")
    
    if unique_stocks > 0:
        # Check status distribution
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM all_stocks_analysis 
            WHERE id IN (SELECT MAX(id) FROM all_stocks_analysis GROUP BY symbol)
            GROUP BY status
        """)
        
        print("  Status distribution (latest per stock):")
        for row in cursor.fetchall():
            print(f"    - {row[0]}: {row[1]}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 6: Check indexes
print("\n[Test 6] Checking Database Indexes...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if config.DATABASE_TYPE == 'postgres':
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public' AND tablename = 'all_stocks_analysis' 
                AND indexname LIKE 'idx_all_stocks%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        else:
            # SQLite: Use sqlite_master
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='all_stocks_analysis' 
                AND name LIKE 'idx_all_stocks%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        if indexes:
            print(f"  [PASS] Found {len(indexes)} indexes for all_stocks_analysis")
            for idx in indexes:
                print(f"    - {idx}")
        else:
            print(f"  [WARN] No indexes found (may affect performance)")
    finally:
        cursor.close()
        conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 7: Test cleanup function
print("\n[Test 7] Testing Cleanup Function...")
try:
    from database import cleanup_all_stocks_analysis
    print("  [PASS] cleanup_all_stocks_analysis function imported successfully")
except Exception as e:
    print(f"  [FAIL] Cannot import cleanup function: {e}")

# Test 8: Check thread_tasks module
print("\n[Test 8] Checking thread_tasks Module...")
try:
    from infrastructure.thread_tasks import analyze_single_stock_bulk, start_bulk_analysis
    print("  [PASS] Bulk analysis functions available")
except Exception as e:
    print(f"  [FAIL] Cannot import bulk analysis functions: {e}")

# Summary
print("\n" + "=" * 60)
print("BACKEND TEST COMPLETE")
print("=" * 60)
print("\nIf all tests passed, backend is ready!")
print("Next: Test frontend and API endpoints")
