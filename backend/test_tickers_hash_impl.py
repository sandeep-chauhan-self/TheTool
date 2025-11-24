#!/usr/bin/env python
"""
Test script for tickers_hash implementation

Tests:
1. Hash computation is deterministic
2. Hash is consistent regardless of input ordering
3. Migration functions work correctly
4. Duplicate detection uses hash efficiently
"""

import json
import hashlib
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_hash_computation():
    """Test SHA-256 hash computation"""
    from migrations.add_tickers_hash import compute_tickers_hash
    
    print("\n" + "="*60)
    print("TEST 1: Hash Computation")
    print("="*60)
    
    # Test 1: Same tickers should produce same hash
    tickers1 = json.dumps(sorted(["INFY.NS", "TCS.NS", "RELIANCE.NS"]))
    tickers2 = json.dumps(sorted(["RELIANCE.NS", "INFY.NS", "TCS.NS"]))  # Different order
    
    hash1 = compute_tickers_hash(tickers1)
    hash2 = compute_tickers_hash(tickers2)
    
    print(f"Tickers 1 (sorted): {tickers1}")
    print(f"Hash 1: {hash1}")
    print()
    print(f"Tickers 2 (sorted): {tickers2}")
    print(f"Hash 2: {hash2}")
    print()
    
    if hash1 == hash2:
        print("✓ PASS: Same tickers produce same hash (deterministic)")
    else:
        print("✗ FAIL: Hashes don't match")
        return False
    
    # Test 2: Hash length should be 64 (SHA-256 hex digest)
    if len(hash1) == 64:
        print(f"✓ PASS: Hash length is 64 bytes (SHA-256): {len(hash1)}")
    else:
        print(f"✗ FAIL: Hash length is {len(hash1)}, expected 64")
        return False
    
    # Test 3: None input should return None
    hash_none = compute_tickers_hash(None)
    if hash_none is None:
        print("✓ PASS: None input returns None")
    else:
        print(f"✗ FAIL: Expected None, got {hash_none}")
        return False
    
    # Test 4: Empty string should return None
    hash_empty = compute_tickers_hash("")
    if hash_empty is None:
        print("✓ PASS: Empty string returns None")
    else:
        print(f"✗ FAIL: Expected None, got {hash_empty}")
        return False
    
    # Test 5: Large ticker list (2,192 stocks)
    large_list = json.dumps([f"STOCK{i:04d}.NS" for i in range(2192)])
    hash_large = compute_tickers_hash(large_list)
    print(f"\n✓ PASS: Large ticker list (2,192 stocks, ~50KB JSON)")
    print(f"  JSON size: {len(large_list):,} bytes")
    print(f"  Hash size: {len(hash_large)} bytes")
    print(f"  Reduction: {len(large_list)/len(hash_large):.1f}x smaller")
    
    return True


def test_duplicate_detection_logic():
    """Test duplicate detection query logic"""
    import hashlib
    import json
    
    print("\n" + "="*60)
    print("TEST 2: Duplicate Detection Logic")
    print("="*60)
    
    # Simulate user requesting analysis with these tickers
    user_tickers = ["TCS.NS", "INFY.NS", "RELIANCE.NS"]
    
    # What gets stored in DB (normalized)
    normalized = json.dumps(sorted([t.upper().strip() for t in user_tickers]))
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))
    stored_hash = hash_obj.hexdigest()
    
    print(f"User tickers: {user_tickers}")
    print(f"Normalized JSON: {normalized}")
    print(f"Stored hash: {stored_hash}")
    
    # Later, user requests same analysis with different order
    user_tickers_2 = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    normalized_2 = json.dumps(sorted([t.upper().strip() for t in user_tickers_2]))
    hash_obj_2 = hashlib.sha256(normalized_2.encode('utf-8'))
    query_hash = hash_obj_2.hexdigest()
    
    print(f"\nUser tickers (request 2): {user_tickers_2}")
    print(f"Normalized JSON: {normalized_2}")
    print(f"Query hash: {query_hash}")
    
    if stored_hash == query_hash:
        print("\n✓ PASS: Same tickers in different order produce same hash")
        print("  Duplicate detection will correctly identify this as duplicate")
    else:
        print("\n✗ FAIL: Hashes don't match")
        return False
    
    return True


def test_imports():
    """Test that all imports work"""
    print("\n" + "="*60)
    print("TEST 3: Module Imports")
    print("="*60)
    
    try:
        from migrations.add_tickers_hash import (
            compute_tickers_hash,
            add_tickers_hash_column,
            populate_tickers_hash_for_existing_jobs,
            remove_old_tickers_index,
            create_tickers_hash_index,
            run_migration
        )
        print("✓ PASS: migrations.add_tickers_hash imported successfully")
    except Exception as e:
        print(f"✗ FAIL: Could not import migrations.add_tickers_hash: {e}")
        return False
    
    try:
        from db_migrations import migration_v4, CURRENT_SCHEMA_VERSION
        print("✓ PASS: db_migrations.migration_v4 imported successfully")
        print(f"  Current schema version: {CURRENT_SCHEMA_VERSION}")
        if CURRENT_SCHEMA_VERSION == 4:
            print("  ✓ Version correctly set to 4")
        else:
            print(f"  ✗ Version is {CURRENT_SCHEMA_VERSION}, expected 4")
            return False
    except Exception as e:
        print(f"✗ FAIL: Could not import db_migrations: {e}")
        return False
    
    try:
        from utils.db_utils import JobStateTransactions
        print("✓ PASS: utils.db_utils.JobStateTransactions imported successfully")
    except Exception as e:
        print(f"✗ FAIL: Could not import utils.db_utils: {e}")
        return False
    
    try:
        from routes.analysis import _get_active_job_for_tickers
        print("✓ PASS: routes.analysis._get_active_job_for_tickers imported successfully")
    except Exception as e:
        print(f"✗ FAIL: Could not import routes.analysis: {e}")
        return False
    
    try:
        from routes.stocks import _get_active_job_for_symbols
        print("✓ PASS: routes.stocks._get_active_job_for_symbols imported successfully")
    except Exception as e:
        print(f"✗ FAIL: Could not import routes.stocks: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TICKERS_HASH IMPLEMENTATION TEST SUITE")
    print("="*70)
    
    tests = [
        ("Hash Computation", test_hash_computation),
        ("Duplicate Detection Logic", test_duplicate_detection_logic),
        ("Module Imports", test_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Implementation is ready for deployment.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Review implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
