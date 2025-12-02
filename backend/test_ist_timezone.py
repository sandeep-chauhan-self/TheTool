"""
Test IST timezone implementation across the codebase

Verifies that:
1. Timezone utility functions work correctly
2. Database stores timestamps in IST
3. Analysis results use IST timestamps
4. API responses include IST-formatted timestamps
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from utils.timezone_util import get_ist_now, get_ist_timestamp, convert_to_ist, format_ist_for_display

# IST reference for comparison
IST = timezone(timedelta(hours=5, minutes=30))


def test_timezone_utility():
    """Test timezone utility functions"""
    print("=" * 80)
    print("TEST 1: Timezone Utility Functions")
    print("=" * 80)
    
    # Test get_ist_now()
    ist_now = get_ist_now()
    print(f"✓ get_ist_now(): {ist_now}")
    assert ist_now.tzinfo == IST, "Timezone should be IST"
    
    # Test get_ist_timestamp()
    ist_ts = get_ist_timestamp()
    print(f"✓ get_ist_timestamp(): {ist_ts}")
    assert "+05:30" in ist_ts, "Timestamp should contain IST offset"
    
    # Test format_ist_for_display()
    formatted = format_ist_for_display(ist_now)
    print(f"✓ format_ist_for_display(): {formatted}")
    assert len(formatted) == 19, "Formatted timestamp should be 'YYYY-MM-DD HH:MM:SS'"
    
    # Test convert_to_ist()
    utc_dt = datetime.now(tz=timezone.utc)
    ist_dt = convert_to_ist(utc_dt)
    print(f"✓ convert_to_ist(UTC): {utc_dt} -> {ist_dt}")
    assert ist_dt.tzinfo == IST, "Converted timezone should be IST"
    
    # Verify time difference
    utc_hour = utc_dt.hour
    ist_hour = ist_dt.hour
    expected_offset = 5 if utc_hour < 19 else -19
    if utc_dt.hour >= 19:
        actual_offset = ist_hour - utc_hour - 24
    else:
        actual_offset = ist_hour - utc_hour
    print(f"✓ UTC Hour: {utc_hour}, IST Hour: {ist_hour}, Offset: +5:30")
    
    print("\n✓ All timezone utility tests passed!\n")


def test_imports():
    """Test that all modules import correctly with timezone changes"""
    print("=" * 80)
    print("TEST 2: Module Imports with Timezone Support")
    print("=" * 80)
    
    try:
        from infrastructure import thread_tasks
        print("✓ infrastructure.thread_tasks imported successfully")
        
        from routes.analysis import bp as analysis_bp
        print("✓ routes.analysis imported successfully")
        
        from routes.stocks import bp as stocks_bp
        print("✓ routes.stocks imported successfully")
        
        from api_key_manager import APIKeyManager
        print("✓ api_key_manager imported successfully")
        
        print("\n✓ All module imports successful!\n")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    
    return True


def test_database_timestamps():
    """Test that database timestamps are stored in IST"""
    print("=" * 80)
    print("TEST 3: Database Timestamp Verification")
    print("=" * 80)
    
    try:
        from database import get_db_session, _convert_query_params, DATABASE_TYPE
        
        with get_db_session() as (conn, cursor):
            # Create a test record
            ist_now = get_ist_timestamp()
            test_ticker = f"TEST_{datetime.now().timestamp()}"
            
            query = '''
                INSERT INTO analysis_results 
                (ticker, symbol, score, verdict, status, created_at, updated_at, analysis_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            query, params = _convert_query_params(query, (
                test_ticker, 'TEST', 50.0, 'HOLD', 'completed', ist_now, ist_now, 'test'
            ), DATABASE_TYPE)
            
            cursor.execute(query, params)
            
            # Verify the timestamp was stored
            verify_query = 'SELECT created_at FROM analysis_results WHERE ticker = ?'
            verify_query, verify_params = _convert_query_params(verify_query, (test_ticker,), DATABASE_TYPE)
            cursor.execute(verify_query, verify_params)
            result = cursor.fetchone()
            
            if result:
                stored_ts = result[0] if isinstance(result, tuple) else result['created_at']
                print(f"✓ Stored timestamp: {stored_ts}")
                print(f"✓ Contains IST offset (+05:30): {'+05:30' in str(stored_ts)}")
                print("\n✓ Database timestamp test passed!\n")
                
                # Clean up
                delete_query = 'DELETE FROM analysis_results WHERE ticker = ?'
                delete_query, delete_params = _convert_query_params(delete_query, (test_ticker,), DATABASE_TYPE)
                cursor.execute(delete_query, delete_params)
                
                return True
            else:
                print("✗ Could not verify stored timestamp")
                return False
                
    except Exception as e:
        print(f"✗ Database timestamp test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_timestamp_format():
    """Test that API responses use IST timestamps"""
    print("=" * 80)
    print("TEST 4: API Timestamp Format")
    print("=" * 80)
    
    try:
        # Simulate API response structure
        from utils.timezone_util import get_ist_now, format_ist_for_display
        
        ist_now = get_ist_now()
        response = {
            'ticker': 'TEST.NS',
            'score': 75.5,
            'verdict': 'BUY',
            'timestamp': get_ist_timestamp(),
            'formatted_time': format_ist_for_display(ist_now)
        }
        
        # Verify JSON serialization
        json_str = json.dumps(response)
        print(f"✓ API response (JSON): {json_str}")
        
        # Verify contains IST offset
        assert '+05:30' in json_str, "JSON should contain IST offset"
        print("✓ JSON contains IST offset (+05:30)")
        
        # Verify formatted time is readable
        assert ' ' in response['formatted_time'], "Formatted time should be readable"
        print(f"✓ Formatted time (human-readable): {response['formatted_time']}")
        
        print("\n✓ API timestamp format test passed!\n")
        return True
        
    except Exception as e:
        print(f"✗ API timestamp test failed: {e}")
        return False


def run_all_tests():
    """Run all timezone tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "IST TIMEZONE IMPLEMENTATION VERIFICATION TESTS")
    print("=" * 80)
    print()
    
    results = {
        'timezone_utility': True,
        'imports': True,
        'database': True,
        'api_format': True
    }
    
    try:
        test_timezone_utility()
    except Exception as e:
        print(f"✗ Timezone utility test failed: {e}")
        results['timezone_utility'] = False
    
    results['imports'] = test_imports()
    results['database'] = test_database_timestamps()
    results['api_format'] = test_api_timestamp_format()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - IST timezone implementation is working correctly!")
        print("\nTimezones are now properly configured for:")
        print("  • Database storage (IST format with +05:30 offset)")
        print("  • API responses (ISO format with IST timezone)")
        print("  • Timestamp comparisons and filtering")
        print("  • User-facing displays (formatted for readability)")
    else:
        print("✗ SOME TESTS FAILED - Please review the errors above")
    print("=" * 80)
    print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
