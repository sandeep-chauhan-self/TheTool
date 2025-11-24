#!/usr/bin/env python
"""
Quick fix: Remove UNIQUE constraint blocking re-analysis

This script immediately drops the problematic UNIQUE index
to allow "Analyze All Stocks" to work without duplicate key errors.

Run this after deploying the migration code if you need immediate fix.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def fix_duplicate_constraint():
    """Apply the fix directly to the database"""
    from database import get_db_connection, query_db
    from config import config
    
    print("\n" + "="*70)
    print("APPLYING FIX: Remove UNIQUE constraint for re-analysis")
    print("="*70)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if config.DATABASE_TYPE == 'postgres':
            print("\nPostgreSQL detected...")
            
            # Check if the UNIQUE index exists
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname = 'idx_analysis_ticker_date'
            """)
            
            if cursor.fetchone():
                print("  Found problematic UNIQUE index: idx_analysis_ticker_date")
                
                # Drop it
                try:
                    cursor.execute("DROP INDEX IF EXISTS idx_analysis_ticker_date")
                    conn.commit()
                    print("  ✓ Successfully dropped UNIQUE index")
                except Exception as e:
                    print(f"  ✗ Error dropping index: {e}")
                    conn.rollback()
                    return False
            else:
                print("  UNIQUE index idx_analysis_ticker_date not found (already removed?)")
            
            # Create regular indices for performance
            try:
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_ticker_created
                    ON analysis_results(ticker, created_at DESC)
                ''')
                print("  ✓ Created index: idx_analysis_ticker_created")
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_created_date
                    ON analysis_results(CAST(created_at AS DATE) DESC)
                ''')
                print("  ✓ Created index: idx_analysis_created_date")
                
                conn.commit()
            except Exception as e:
                print(f"  ✗ Error creating indices: {e}")
                conn.rollback()
                return False
        
        else:
            print("\nSQLite detected...")
            
            # Drop the index
            try:
                cursor.execute("DROP INDEX IF EXISTS idx_analysis_ticker_date")
                conn.commit()
                print("  ✓ Dropped UNIQUE index if it existed")
            except Exception as e:
                print(f"  Note: {e}")
                conn.rollback()
            
            # Create regular indices
            try:
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_ticker_created
                    ON analysis_results(ticker, created_at DESC)
                ''')
                print("  ✓ Created index: idx_analysis_ticker_created")
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_analysis_created_date
                    ON analysis_results(CAST(created_at AS DATE) DESC)
                ''')
                print("  ✓ Created index: idx_analysis_created_date")
                
                conn.commit()
            except Exception as e:
                print(f"  ✗ Error creating indices: {e}")
                conn.rollback()
                return False
        
        conn.close()
        
        print("\n" + "="*70)
        print("✓ FIX APPLIED SUCCESSFULLY")
        print("="*70)
        print("\nYou can now:")
        print("  1. Click 'Analyze All Stocks' again")
        print("  2. Re-run analysis on the same day without duplicate key errors")
        print("  3. Analyze multiple times without restrictions")
        print("\nNote: On next app startup, migration v5 will run automatically")
        return True
        
    except Exception as e:
        print(f"\n✗ Error applying fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_duplicate_constraint()
    sys.exit(0 if success else 1)
