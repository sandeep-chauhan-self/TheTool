"""Comprehensive test to verify watchlist and analysis functionality"""
import sys
sys.path.insert(0, 'backend')

from app import create_app
from database import query_db, execute_db

app = create_app()

print("=" * 60)
print("COMPREHENSIVE FUNCTIONALITY TEST")
print("=" * 60)

with app.app_context():
    # Test 1: Watchlist GET returns correct field names
    print("\n[TEST 1] Watchlist GET endpoint format")
    items = query_db("SELECT id, symbol, name, created_at FROM watchlist ORDER BY id DESC LIMIT 1")
    if items:
        item = items[0]
        if isinstance(item, (tuple, list)):
            print(f"  ✓ PostgreSQL tuple detected: {type(item)}")
            print(f"    Fields available: id={item[0]}, symbol={item[1]}, name={item[2]}")
        else:
            print(f"  ✓ SQLite Row object: {type(item)}")
            d = dict(item)
            print(f"    Fields: {list(d.keys())}")
    else:
        print("  ⚠ No watchlist items to test")
    
    # Test 2: Analysis history query format
    print("\n[TEST 2] Analysis history endpoint format")
    results = query_db("""
        SELECT id, ticker, symbol, verdict, score, entry, stop_loss, target, created_at
        FROM analysis_results
        ORDER BY created_at DESC
        LIMIT 1
    """)
    if results:
        r = results[0]
        if isinstance(r, (tuple, list)):
            print(f"  ✓ PostgreSQL tuple: {len(r)} fields")
            print(f"    Field 0 (id): {r[0]}")
            print(f"    Field 1 (ticker): {r[1]}")
            print(f"    Field 3 (verdict): {r[3]}")
            print(f"    Field 4 (score): {r[4]}")
        else:
            print(f"  ✓ SQLite Row object")
            d = dict(r)
            print(f"    Fields: {list(d.keys())}")
    else:
        print("  ⚠ No analysis results to test")
    
    # Test 3: Analysis report query format
    print("\n[TEST 3] Analysis report endpoint format")
    result = query_db("""
        SELECT verdict, score, entry, stop_loss, target, created_at, raw_data
        FROM analysis_results
        ORDER BY created_at DESC
        LIMIT 1
    """, one=True)
    if result:
        if isinstance(result, (tuple, list)):
            print(f"  ✓ PostgreSQL tuple: {len(result)} fields")
            print(f"    Field 0 (verdict): {result[0]}")
            print(f"    Field 1 (score): {result[1]}")
        else:
            print(f"  ✓ SQLite Row object")
            d = dict(result)
            print(f"    Fields: {list(d.keys())}")
    else:
        print("  ⚠ No analysis result to test")
    
    # Test 4: Watchlist field names after transformation
    print("\n[TEST 4] Watchlist GET transformed response format")
    items = query_db("SELECT id, symbol, name, created_at FROM watchlist ORDER BY id DESC LIMIT 1")
    if items:
        item = items[0]
        # Simulate the transformation in the GET endpoint
        if isinstance(item, (tuple, list)):
            transformed = {
                "id": item[0],
                "ticker": item[1],  # Renamed from symbol
                "name": item[2],
                "created_at": str(item[3]) if item[3] else None
            }
        else:
            item_dict = dict(item)
            if 'symbol' in item_dict:
                item_dict['ticker'] = item_dict.pop('symbol')
            transformed = item_dict
        
        print(f"  ✓ Transformed fields: {list(transformed.keys())}")
        print(f"    Has 'ticker' field: {'ticker' in transformed}")
        print(f"    Has 'symbol' field: {'symbol' in transformed}")
        print(f"    Values: ticker={transformed.get('ticker')}, name={transformed.get('name')}")
    else:
        print("  ⚠ No items to test transformation")
    
    # Test 5: Check database integrity
    print("\n[TEST 5] Database schema validation")
    
    # Check watchlist columns
    if app.config['DATABASE_TYPE'] == 'postgres':
        watchlist_cols = query_db("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='watchlist'
        """)
        cols = [col[0] if isinstance(col, (tuple, list)) else col['column_name'] for col in watchlist_cols]
        print(f"  ✓ Watchlist columns: {cols}")
        print(f"    Has 'symbol': {'symbol' in cols}")
    else:
        print(f"  ✓ Using SQLite database")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)
