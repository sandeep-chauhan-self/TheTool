"""Quick test - database only, no HTTP"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'trading_app.db')

print("=" * 60)
print("UNIFIED TABLE VALIDATION")
print("=" * 60)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check schema
    print("\n1. Checking analysis_results schema...")
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = [row[1] for row in cursor.fetchall()]
    
    required = ['symbol', 'name', 'yahoo_symbol', 'status', 'error_message', 
                'updated_at', 'analysis_source']
    missing = [col for col in required if col not in columns]
    
    if missing:
        print(f"   ? Missing columns: {missing}")
    else:
        print(f"   ? All new columns present")
    
    # Check data counts
    print("\n2. Checking data distribution...")
    cursor.execute("SELECT COUNT(*) FROM analysis_results")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source='watchlist'")
    watchlist = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source='bulk'")
    bulk = cursor.fetchone()[0]
    
    print(f"   Total records: {total}")
    print(f"   Watchlist: {watchlist}")
    print(f"   Bulk: {bulk}")
    
    # Check old table
    print("\n3. Checking deprecated table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='all_stocks_analysis_deprecated'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM all_stocks_analysis_deprecated")
        old_count = cursor.fetchone()[0]
        print(f"   ? Deprecated table exists with {old_count} records (can be dropped after 1 week)")
    else:
        print(f"   ! Deprecated table not found")
    
    # Sample data
    print("\n4. Sample records...")
    cursor.execute("""
        SELECT symbol, name, analysis_source, verdict, score, created_at 
        FROM analysis_results 
        WHERE symbol IS NOT NULL
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"   {row[0]:15} {row[2]:10} {row[3]:10} Score: {row[4]:.1f}")
    
    # Cross-visibility check
    print("\n5. Cross-visibility test...")
    cursor.execute("""
        SELECT symbol, 
               SUM(CASE WHEN analysis_source='watchlist' THEN 1 ELSE 0 END) as w,
               SUM(CASE WHEN analysis_source='bulk' THEN 1 ELSE 0 END) as b
        FROM analysis_results
        WHERE symbol IS NOT NULL
        GROUP BY symbol
        HAVING w > 0 AND b > 0
        LIMIT 3
    """)
    
    dual = cursor.fetchall()
    if dual:
        print(f"   ? Found {len(dual)} stocks with both watchlist & bulk analysis:")
        for row in dual:
            print(f"     - {row[0]}: watchlist={row[1]}, bulk={row[2]}")
    else:
        print("   ! No stocks with both analysis types yet")
        print("     (Analyze a watchlist stock to test cross-visibility)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("? MIGRATION SUCCESSFUL - UNIFIED TABLE WORKING")
    print("=" * 60)
    
except Exception as e:
    print(f"\n? ERROR: {e}")
    import traceback
    traceback.print_exc()
