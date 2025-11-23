#!/usr/bin/env python
"""
Verify PostgreSQL connection and database schema
Run this to check if PostgreSQL is properly configured
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main verification function"""
    from config import config
    
    print("=" * 80)
    print("PostgreSQL Connection Verification")
    print("=" * 80)
    
    # Check database type
    print(f"\n1. Database Type Detection:")
    print(f"   DATABASE_URL set: {bool(config.DATABASE_URL)}")
    print(f"   Database type: {config.DATABASE_TYPE.upper()}")
    
    if config.DATABASE_TYPE == 'sqlite':
        print(f"   SQLite path: {config.DB_PATH}")
        print("\n   ⚠️  SQLite is being used (local development)")
        print("   For Railway, DATABASE_URL must be set to use PostgreSQL")
        return
    
    # Try PostgreSQL connection
    print(f"\n2. Attempting PostgreSQL Connection...")
    try:
        import psycopg2
        
        conn = psycopg2.connect(config.DATABASE_URL)
        cursor = conn.cursor()
        print(f"   ✓ Connected to PostgreSQL successfully!")
        
        # Check tables
        print(f"\n3. Checking Database Schema...")
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"     - {table[0]}")
        
        # Check analysis_jobs table
        print(f"\n4. Checking analysis_jobs Table...")
        cursor.execute("SELECT COUNT(*) FROM analysis_jobs")
        job_count = cursor.fetchone()[0]
        print(f"   Total jobs in database: {job_count}")
        
        # Check analysis_results table
        print(f"\n5. Checking analysis_results Table...")
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        result_count = cursor.fetchone()[0]
        print(f"   Total analysis results: {result_count}")
        
        # Check watchlist table
        print(f"\n6. Checking watchlist Table...")
        cursor.execute("SELECT COUNT(*) FROM watchlist")
        watchlist_count = cursor.fetchone()[0]
        print(f"   Total stocks in watchlist: {watchlist_count}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✓ PostgreSQL is properly configured and working!")
        print("=" * 80)
        
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n" + "=" * 80)
        print("ERROR: PostgreSQL Connection Failed")
        print("=" * 80)
        print("\nTroubleshooting:")
        print("1. Check that DATABASE_URL is set in Railway Variables")
        print("2. Verify PostgreSQL service is running")
        print("3. Check connection string format (should start with postgresql://)")
        print("\nTo set DATABASE_URL in Railway:")
        print("  Railway Dashboard → Backend Service → Variables")
        print("  Add: DATABASE_URL = ${Postgres.DATABASE_URL}")
        sys.exit(1)


if __name__ == '__main__':
    main()
