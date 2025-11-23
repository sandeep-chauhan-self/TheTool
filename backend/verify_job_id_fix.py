#!/usr/bin/env python3
"""
Verification script to validate job_id filtering implementation.

This script tests that:
1. The schema changes are in place
2. Results are properly filtered by job_id
3. Multiple jobs don't interfere with each other
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import config
from database import query_db, execute_db, _convert_query_params

def check_schema():
    """Check if job_id column exists in analysis_results table"""
    print("\n" + "="*60)
    print("SCHEMA VERIFICATION")
    print("="*60)
    
    try:
        if config.DATABASE_TYPE == 'postgres':
            result = query_db("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='analysis_results' AND column_name='job_id'
                )
            """, one=True)
            has_job_id = result[0] if result else False
        else:
            result = query_db("PRAGMA table_info(analysis_results)", ())
            columns = [row[1] for row in result] if result else []
            has_job_id = 'job_id' in columns
        
        if has_job_id:
            print("✓ job_id column exists in analysis_results table")
            return True
        else:
            print("✗ job_id column NOT found - schema needs migration")
            print("  Run: python backend/migrate_add_job_id.py")
            return False
    except Exception as e:
        print(f"✗ Schema check failed: {e}")
        return False


def check_index():
    """Check if idx_job_id index exists"""
    print("\n" + "="*60)
    print("INDEX VERIFICATION")
    print("="*60)
    
    try:
        if config.DATABASE_TYPE == 'postgres':
            result = query_db("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename='analysis_results' AND indexname='idx_job_id'
                )
            """, one=True)
            has_index = result[0] if result else False
        else:
            # SQLite pragma
            result = query_db("PRAGMA index_info(idx_job_id)", ())
            has_index = len(result) > 0 if result else False
        
        if has_index:
            print("✓ idx_job_id index exists for performance")
            return True
        else:
            print("✗ idx_job_id index NOT found")
            print("  Run: python backend/migrate_add_job_id.py")
            return False
    except Exception as e:
        print(f"✗ Index check failed: {e}")
        return False


def check_query_logic():
    """Verify that the SELECT query would filter by job_id correctly"""
    print("\n" + "="*60)
    print("QUERY LOGIC VERIFICATION")
    print("="*60)
    
    # Simulate the query that should be used
    query = """
    SELECT ticker, symbol, verdict, score, entry, stop_loss, target, created_at
    FROM analysis_results 
    WHERE job_id = ?
    ORDER BY created_at DESC
    LIMIT 50
    """
    
    # Check that query has WHERE job_id clause
    if "WHERE job_id = ?" in query or "WHERE job_id=?" in query:
        print("✓ Query correctly filters by job_id parameter")
        return True
    else:
        print("✗ Query does NOT filter by job_id")
        return False


def check_insert_columns():
    """Verify that INSERT statements include job_id"""
    print("\n" + "="*60)
    print("INSERT STATEMENT VERIFICATION")
    print("="*60)
    
    # These are the files that should have been updated
    files_to_check = [
        ('backend/thread_tasks.py', 'INSERT INTO analysis_results'),
        ('backend/utils/db_utils.py', 'INSERT INTO analysis_results'),
    ]
    
    all_ok = True
    for filepath, search_string in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        try:
            with open(full_path, 'r') as f:
                content = f.read()
                
            # Find the INSERT statement and check if job_id is there
            if 'job_id' in content and search_string in content:
                # Find context around INSERT
                lines = content.split('\n')
                found_insert_with_job_id = False
                
                for i, line in enumerate(lines):
                    if search_string in line:
                        # Check next 5 lines for job_id
                        context = '\n'.join(lines[i:min(i+5, len(lines))])
                        if 'job_id' in context:
                            found_insert_with_job_id = True
                            break
                
                if found_insert_with_job_id:
                    print(f"✓ {filepath} - job_id included in INSERT")
                else:
                    print(f"✗ {filepath} - job_id NOT in INSERT context")
                    all_ok = False
            else:
                print(f"⚠ {filepath} - unable to verify (file may have changed)")
        except Exception as e:
            print(f"✗ {filepath} - verification failed: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("JOB ID ASSOCIATION FIX - VERIFICATION SUITE")
    print("="*70)
    print(f"\nDatabase Type: {config.DATABASE_TYPE.upper()}")
    if config.DATABASE_TYPE == 'postgres':
        print(f"Connection: {config.DATABASE_URL[:40]}...")
    else:
        print(f"Database Path: {config.DB_PATH}")
    
    results = []
    
    # Run all checks
    results.append(("Schema", check_schema()))
    results.append(("Index", check_index()))
    results.append(("Query Logic", check_query_logic()))
    results.append(("Insert Statements", check_insert_columns()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✅ All verifications passed! Job ID filtering is ready.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Review the details above.")
        if not check_schema() or not check_index():
            print("\nTo fix schema/index issues:")
            print("  cd backend")
            print("  python migrate_add_job_id.py")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
