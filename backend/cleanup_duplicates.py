#!/usr/bin/env python3
"""
Cleanup Script: Remove duplicate analysis records that violate unique constraint.

Issue: Database has duplicate (ticker, date, strategy_id) combinations
that prevent creating the unique index for migration v8.

Solution: Delete older duplicates and keep only the most recent analysis per (ticker, date, strategy_id).
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Get PostgreSQL connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise Exception("DATABASE_URL not set!")
    
    # Fix PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = 'postgresql://' + database_url[11:]
    
    return psycopg2.connect(database_url)

def cleanup_duplicates():
    """Remove duplicate records"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("🔍 Analyzing duplicate records...")
        
        # Check for duplicates
        cursor.execute('''
            SELECT ticker, CAST(created_at AS DATE) as analysis_date, strategy_id, COUNT(*) as count
            FROM analysis_results
            GROUP BY ticker, CAST(created_at AS DATE), strategy_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        
        duplicates = cursor.fetchall()
        if not duplicates:
            print("✓ No duplicates found!")
            conn.close()
            return True
        
        print(f"\n📊 Found {len(duplicates)} groups with duplicates:")
        for ticker, analysis_date, strategy_id, count in duplicates[:10]:  # Show first 10
            print(f"   • {ticker} ({analysis_date}) Strategy {strategy_id or 1}: {count} records")
        
        if len(duplicates) > 10:
            print(f"   ... and {len(duplicates) - 10} more")
        
        print(f"\n🧹 Removing duplicates (keeping most recent per group)...")
        
        # Delete older duplicates, keep most recent by ID
        cursor.execute('''
            DELETE FROM analysis_results a
            WHERE a.id NOT IN (
                SELECT MAX(b.id)
                FROM analysis_results b
                WHERE b.ticker = a.ticker
                  AND CAST(b.created_at AS DATE) = CAST(a.created_at AS DATE)
                  AND COALESCE(b.strategy_id, 1) = COALESCE(a.strategy_id, 1)
                GROUP BY b.ticker, CAST(b.created_at AS DATE), COALESCE(b.strategy_id, 1)
            )
        ''')
        
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"✓ Deleted {deleted} duplicate records")
        
        # Verify
        cursor.execute('''
            SELECT COUNT(*)
            FROM (
                SELECT ticker, CAST(created_at AS DATE), strategy_id
                FROM analysis_results
                GROUP BY ticker, CAST(created_at AS DATE), strategy_id
                HAVING COUNT(*) > 1
            ) t
        ''')
        
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            print("✓ Duplicate cleanup verified - database is clean!")
        else:
            print(f"⚠ Still {remaining} duplicate groups remaining")
        
        conn.close()
        return remaining == 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("ANALYSIS RESULTS DUPLICATE CLEANUP")
    print("=" * 60)
    print()
    
    success = cleanup_duplicates()
    
    print()
    if success:
        print("✓ Cleanup completed successfully!")
        print("  The database is now ready for the unique index constraint.")
    else:
        print("✗ Cleanup failed or incomplete.")
        print("  Check the error messages above.")
    
    print()
    print("=" * 60)
