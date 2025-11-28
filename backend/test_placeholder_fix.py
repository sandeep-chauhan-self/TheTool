#!/usr/bin/env python3
"""
Test script to verify the placeholder conversion fix works correctly
This ensures that SQLite connections use ? and PostgreSQL connections use %s
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from database import _convert_query_params, _detect_connection_type, get_db_connection, DATABASE_TYPE

def test_sqlite_connection_detection():
    """Test that SQLite connections are properly detected"""
    print("\n=== Testing SQLite Connection Detection ===")
    conn = sqlite3.connect(':memory:')
    detected_type = _detect_connection_type(conn)
    print(f"SQLite detected as: {detected_type}")
    assert detected_type == 'sqlite', f"Expected 'sqlite' but got '{detected_type}'"
    conn.close()
    print("[OK] SQLite detection passed")

def test_placeholder_conversion_for_sqlite():
    """Test that SQLite queries keep ? placeholders"""
    print("\n=== Testing Placeholder Conversion for SQLite ===")
    query = "INSERT INTO analysis_results (ticker, score) VALUES (?, ?)"
    args = ('AAPL', 95.5)
    
    converted_query, converted_args = _convert_query_params(query, args, 'sqlite')
    print(f"Original:  {query}")
    print(f"Converted: {converted_query}")
    print(f"Args:      {converted_args}")
    
    assert converted_query == query, "SQLite query should not be converted"
    assert '?' in converted_query, "SQLite query should contain ?"
    assert '%s' not in converted_query, "SQLite query should NOT contain %s"
    print("[OK] SQLite placeholder conversion passed")

def test_placeholder_conversion_for_postgres():
    """Test that PostgreSQL queries convert ? to %s"""
    print("\n=== Testing Placeholder Conversion for PostgreSQL ===")
    query = "INSERT INTO analysis_results (ticker, score) VALUES (?, ?)"
    args = ('AAPL', 95.5)
    
    converted_query, converted_args = _convert_query_params(query, args, 'postgres')
    print(f"Original:  {query}")
    print(f"Converted: {converted_query}")
    print(f"Args:      {converted_args}")
    
    expected_query = "INSERT INTO analysis_results (ticker, score) VALUES (%s, %s)"
    assert converted_query == expected_query, f"Expected '{expected_query}' but got '{converted_query}'"
    assert '%s' in converted_query, "PostgreSQL query should contain %s"
    assert '?' not in converted_query, "PostgreSQL query should NOT contain ?"
    print("[OK] PostgreSQL placeholder conversion passed")

def test_actual_sqlite_execution():
    """Test that actual SQLite execution works with the fix"""
    print("\n=== Testing Actual SQLite Execution ===")
    
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create a test table
    cursor.execute('''
        CREATE TABLE test_results (
            id INTEGER PRIMARY KEY,
            ticker TEXT,
            score REAL
        )
    ''')
    
    # Test insert with converted parameters
    query = "INSERT INTO test_results (ticker, score) VALUES (?, ?)"
    args = ('RELIANCE', 85.5)
    
    # Detect actual connection type
    actual_type = _detect_connection_type(conn)
    converted_query, converted_args = _convert_query_params(query, args, actual_type)
    
    print(f"Connection type: {actual_type}")
    print(f"Query: {converted_query}")
    print(f"Args: {converted_args}")
    
    # Execute with converted parameters
    cursor.execute(converted_query, converted_args)
    conn.commit()
    
    # Verify insertion
    cursor.execute("SELECT * FROM test_results WHERE ticker = ?", ('RELIANCE',))
    result = cursor.fetchone()
    
    assert result is not None, "Failed to insert/retrieve test data"
    assert result[1] == 'RELIANCE', "Ticker mismatch"
    assert result[2] == 85.5, "Score mismatch"
    
    conn.close()
    print("[OK] Actual SQLite execution passed")

def main():
    print("=" * 60)
    print("TESTING PLACEHOLDER CONVERSION FIX")
    print("=" * 60)
    print(f"Current DATABASE_TYPE: {DATABASE_TYPE}")
    
    try:
        test_sqlite_connection_detection()
        test_placeholder_conversion_for_sqlite()
        test_placeholder_conversion_for_postgres()
        test_actual_sqlite_execution()
        
        print("\n" + "=" * 60)
        print("[OK] ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
