#!/usr/bin/env python3
"""
Production database cleanup script - Run this with: railway run python cleanup_prod_watchlist.py

This script cleans up orphaned or duplicate watchlist entries from the production PostgreSQL database.
"""
import os
import sys
import psycopg2

def connect_to_db():
    """Connect to PostgreSQL database from Railway"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Make sure to run this script with: railway run python cleanup_prod_watchlist.py")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

def main():
    """Main cleanup function"""
    print("=== PRODUCTION DATABASE CLEANUP ===\n")
    
    conn = connect_to_db()
    cur = conn.cursor()
    
    try:
        # Step 1: List all watchlist items
        print("STEP 1: Current watchlist items")
        print("-" * 50)
        cur.execute("SELECT id, symbol, name, created_at FROM watchlist ORDER BY created_at DESC")
        rows = cur.fetchall()
        print(f"Total items: {len(rows)}\n")
        for row in rows:
            print(f"  ID {row[0]}: {row[1]} - {row[2]} (created: {row[3]})")
        
        # Step 2: Check for duplicates
        print("\nSTEP 2: Checking for duplicate symbols")
        print("-" * 50)
        cur.execute("""
            SELECT LOWER(symbol), COUNT(*) as cnt 
            FROM watchlist 
            GROUP BY LOWER(symbol) 
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print(f"Found {len(duplicates)} duplicate symbols:")
            for dup in duplicates:
                print(f"  {dup[0]}: {dup[1]} entries")
        else:
            print("No duplicates found")
        
        # Step 3: Optional: Delete specific symbol
        if len(rows) > 0:
            print("\nSTEP 3: Options for cleanup")
            print("-" * 50)
            print("To delete all RELIANCE entries, run:")
            print("  railway run python -c \"import psycopg2, os; c=psycopg2.connect(os.getenv('DATABASE_URL')); cur=c.cursor(); cur.execute('DELETE FROM watchlist WHERE LOWER(symbol) LIKE %s', ('%reliance%',)); c.commit(); print(f'Deleted {cur.rowcount} rows')\"")
            print("\nTo delete entry by ID, run:")
            print("  railway run python -c \"import psycopg2, os; c=psycopg2.connect(os.getenv('DATABASE_URL')); cur=c.cursor(); cur.execute('DELETE FROM watchlist WHERE id = %s', (ID_HERE,)); c.commit(); print(f'Deleted {cur.rowcount} rows')\"")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
