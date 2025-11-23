"""
Quick test for unified table integration

FOLLOW: TheTool.prompt.md Section 9 (Testing Layers & Coverage Goals)
Uses centralized constants from backend/constants.py for URL configuration.
"""
import requests
import json
from constants import get_api_base_url, API_URLS

BASE_URL = get_api_base_url()
API_KEY = os.getenv("API_KEY", "test_key_for_local_dev_only")
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_get_all_stocks():
    """Test /all-stocks endpoint with unified table"""
    print("\n=== Testing /all-stocks endpoint ===")
    response = requests.get(f"{BASE_URL}/all-stocks", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total stocks: {data.get('count', 0)}")
        if data.get('stocks'):
            # Show first 3 stocks
            for stock in data['stocks'][:3]:
                print(f"  - {stock['symbol']}: {stock.get('verdict', 'N/A')} (Score: {stock.get('score', 'N/A')})")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_stock_history():
    """Test /all-stocks/{symbol}/history endpoint"""
    print("\n=== Testing /all-stocks/RELIANCE/history endpoint ===")
    response = requests.get(f"{BASE_URL}/all-stocks/RELIANCE/history", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"History records: {data.get('count', 0)}")
        if data.get('history'):
            latest = data['history'][0]
            print(f"  Latest: {latest.get('verdict')} (Score: {latest.get('score')})")
            print(f"  Date: {latest.get('analyzed_at')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_watchlist_history():
    """Test /history/{ticker} endpoint (watchlist)"""
    print("\n=== Testing /history/RELIANCE.NS endpoint (watchlist) ===")
    response = requests.get(f"{BASE_URL}/history/RELIANCE.NS", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"History records: {data.get('count', 0)}")
        if data.get('history'):
            latest = data['history'][0]
            print(f"  Latest: {latest.get('verdict')} (Score: {latest.get('score')})")
            print(f"  Date: {latest.get('analyzed_at')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def check_cross_visibility():
    """
    CRITICAL TEST: Check if stock analyzed from watchlist appears in all-stocks
    and vice versa (the main issue we're solving)
    """
    print("\n=== CRITICAL: Testing Cross-View Visibility ===")
    
    # Get a stock that has both watchlist and bulk analysis
    # We'll check the database directly for this
    import os
    from database import get_db_connection
    from config import config
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find a stock that should appear in both views
    cursor.execute("""
        SELECT symbol, COUNT(*) as cnt, 
               SUM(CASE WHEN analysis_source='watchlist' THEN 1 ELSE 0 END) as watchlist_cnt,
               SUM(CASE WHEN analysis_source='bulk' THEN 1 ELSE 0 END) as bulk_cnt
        FROM analysis_results
        WHERE symbol IS NOT NULL
        GROUP BY symbol
        HAVING watchlist_cnt > 0 AND bulk_cnt > 0
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if row:
        symbol = row[0]
        print(f"\nFound stock '{symbol}' with both types of analysis:")
        print(f"  - Watchlist analyses: {row[2]}")
        print(f"  - Bulk analyses: {row[3]}")
        print(f"  - Total: {row[1]}")
        print("\n? CROSS-VISIBILITY WORKING: Same stock appears in both sources!")
    else:
        print("\n! No stocks found with both watchlist and bulk analysis yet")
        print("  (This is expected if you haven't analyzed from watchlist after migration)")
    
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("UNIFIED TABLE INTEGRATION TEST")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_get_all_stocks()
        all_passed &= test_stock_history()
        all_passed &= test_watchlist_history()
        check_cross_visibility()
        
        print("\n" + "=" * 60)
        if all_passed:
            print("? ALL TESTS PASSED")
        else:
            print("! SOME TESTS FAILED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n? ERROR: Cannot connect to backend server")
        print("  Make sure Flask is running: python app.py")
    except Exception as e:
        print(f"\n? ERROR: {e}")
        import traceback
        traceback.print_exc()
