#!/usr/bin/env python3
"""
Database migration script to add job_id column to analysis_results table.

This script safely adds the job_id column and its index to existing databases
without losing data. It handles both SQLite and PostgreSQL.

Usage:
    python migrate_add_job_id.py

The script will:
1. Check if the column already exists (skip if it does)
2. Add the job_id column with NULL default
3. Create an index on job_id for performance
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
    """Add job_id column to SQLite database"""
    db_path = config.DB_PATH
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(analysis_results)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'job_id' in columns:
            print("✓ job_id column already exists in SQLite database")
            cursor.close()
            conn.close()
            return True
        
        print("Adding job_id column to SQLite analysis_results table...")
        
        # Add job_id column
        cursor.execute("""
            ALTER TABLE analysis_results 
            ADD COLUMN job_id TEXT
        """)
        print("✓ job_id column added")
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_id 
            ON analysis_results(job_id)
        """)
        print("✓ idx_job_id index created")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n✅ SQLite migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ SQLite migration failed: {e}")
        return False


def migrate_postgres():
    """Add job_id column to PostgreSQL database"""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='analysis_results' AND column_name='job_id'
            )
        """)
        
        if cursor.fetchone()[0]:
            print("✓ job_id column already exists in PostgreSQL database")
            cursor.close()
            conn.close()
            return True
        
        print("Adding job_id column to PostgreSQL analysis_results table...")
        
        # Add job_id column
        cursor.execute("""
            ALTER TABLE analysis_results 
            ADD COLUMN job_id TEXT
        """)
        print("✓ job_id column added")
        
        # Create index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_id 
            ON analysis_results(job_id)
        """)
        print("✓ idx_job_id index created")
        
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
    print("Database Migration: Add job_id to analysis_results")
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
        print("\n✅ All migrations completed successfully!")
        print("Your application is now ready to use job_id filtering.")
        return 0
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
