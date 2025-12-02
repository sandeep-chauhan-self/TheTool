#!/usr/bin/env python3
"""
Database migration script to add tickers_json column to analysis_jobs table.

This script safely adds the tickers_json column and its index to existing databases
without losing data. It handles both SQLite and PostgreSQL.

Usage:
    python migrate_add_tickers_json.py

The script will:
1. Check if the column already exists (skip if it does)
2. Add the tickers_json column with NULL default
3. Create an index on (tickers_json, status) for duplicate detection queries
4. Report success or any errors
"""

import os
import sys
from config import config

# Import database support
if config.DATABASE_TYPE == 'postgres':
    import psycopg2
else:
    import sqlite3

def migrate_sqlite():
    """Add tickers_json column to SQLite database"""
    db_path = config.DB_PATH
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(analysis_jobs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'tickers_json' in columns:
            print("✓ tickers_json column already exists in SQLite database")
            cursor.close()
            conn.close()
            return True
        
        print("Adding tickers_json column to SQLite analysis_jobs table...")
        
        # Add tickers_json column
        cursor.execute("""
            ALTER TABLE analysis_jobs 
            ADD COLUMN tickers_json TEXT
        """)
        print("✓ tickers_json column added")
        
        # NOTE: No indexes created for analysis_jobs due to 8KB index limit overflow
        # when combining tickers_json (large JSON string) with other columns.
        # Job status queries will use table scan (acceptable - analysis_jobs is small,
        # typically <100 rows in active use). This is a deliberate design decision.
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ SQLite migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ SQLite migration failed: {e}")
        return False


def migrate_postgres():
    """Add tickers_json column to PostgreSQL database"""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='analysis_jobs' AND column_name='tickers_json'
            )
        """)
        
        if cursor.fetchone()[0]:
            print("✓ tickers_json column already exists in PostgreSQL database")
            cursor.close()
            conn.close()
            return True
        
        print("Adding tickers_json column to PostgreSQL analysis_jobs table...")
        
        # Add tickers_json column
        cursor.execute("""
            ALTER TABLE analysis_jobs 
            ADD COLUMN tickers_json TEXT
        """)
        print("✓ tickers_json column added")
        
        # NOTE: No indexes created for analysis_jobs (see SQLite decision above).
        # Keeping consistency between dev (SQLite) and production (PostgreSQL).
        # Job status queries will use table scan.
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ PostgreSQL migration completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure DATABASE_URL is set correctly")
        print("2. Check that PostgreSQL service is running")
        print("3. Verify connection string format")
        return False
    except Exception as e:
        print(f"\n❌ PostgreSQL migration failed: {e}")
        return False


def main():
    """Run migration based on database type"""
    print("=" * 60)
    print("Database Migration: Add tickers_json to analysis_jobs")
    print("=" * 60)
    print(f"\nDatabase Type: {config.DATABASE_TYPE.upper()}")
    
    if config.DATABASE_TYPE == 'postgres':
        print(f"Connection URL: {config.DATABASE_URL[:50]}...")
        success = migrate_postgres()
    else:
        print(f"Database Path: {config.DB_PATH}")
        success = migrate_sqlite()
    
    print("=" * 60)
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nWhat changed:")
        print("- Added 'tickers_json' column to analysis_jobs table")
        print("- No indexes created (table scan used for small analysis_jobs table)")
        print("- Normalized tickers stored with each job for duplicate detection")
        return 0
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
