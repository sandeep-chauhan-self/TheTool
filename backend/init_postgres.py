#!/usr/bin/env python
"""
Initialize PostgreSQL database schema on Railway

Usage:
  python init_postgres.py

This script:
1. Checks DATABASE_URL environment variable
2. Connects to PostgreSQL on Railway
3. Creates all required tables and indexes
4. Verifies successful schema creation

Environment Variables Required:
  DATABASE_URL: PostgreSQL connection string (set by Railway automatically)
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main initialization function"""
    import psycopg2
    
    # Get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        print("This script requires DATABASE_URL to connect to PostgreSQL on Railway.")
        print("\nTo set up:")
        print("1. Go to Railway Dashboard → Your TheTool project")
        print("2. Click Variables tab")
        print("3. Add: DATABASE_URL = ${Postgres.DATABASE_URL}")
        sys.exit(1)
    
    print(f"Connecting to PostgreSQL...")
    print(f"Database URL: {database_url[:50]}...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✓ Connection successful!")
        print("\nCreating tables...")
        
        # Watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL,
                symbol TEXT UNIQUE NOT NULL,
                notes TEXT,
                name TEXT,
                user_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ watchlist table created")
        
        # Analysis results table (UNIFIED)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL,
                symbol TEXT,
                name TEXT,
                yahoo_symbol TEXT,
                score REAL NOT NULL,
                verdict TEXT NOT NULL,
                entry REAL,
                stop_loss REAL,
                target REAL,
                entry_method TEXT,
                data_source TEXT,
                is_demo_data BOOLEAN DEFAULT FALSE,
                raw_data TEXT,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                analysis_source TEXT
            )
        ''')
        print("✓ analysis_results table created")
        
        # Job tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                successful INTEGER DEFAULT 0,
                errors TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        print("✓ analysis_jobs table created")
        
        print("\nCreating indexes...")
        
        # Create indexes for analysis_results
        indexes = [
            ('idx_ticker', 'analysis_results(ticker)'),
            ('idx_created_at', 'analysis_results(created_at)'),
            ('idx_ticker_created', 'analysis_results(ticker, created_at DESC)'),
            ('idx_symbol', 'analysis_results(symbol)'),
            ('idx_yahoo_symbol', 'analysis_results(yahoo_symbol)'),
            ('idx_status', 'analysis_results(status)'),
            ('idx_analysis_source', 'analysis_results(analysis_source)'),
            ('idx_symbol_created', 'analysis_results(symbol, created_at DESC)'),
            ('idx_source_symbol', 'analysis_results(analysis_source, symbol)'),
            ('idx_updated_at', 'analysis_results(updated_at)'),
            ('idx_job_status', 'analysis_jobs(status)'),
        ]
        
        for idx_name, idx_def in indexes:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}')
            print(f"✓ {idx_name} created")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print("SUCCESS! PostgreSQL schema initialized successfully!")
        print("=" * 60)
        print("\nYour database is ready. Your app will now:")
        print("1. Detect DATABASE_URL from Railway environment")
        print("2. Use PostgreSQL instead of SQLite")
        print("3. Persist data across deployments")
        print("\nRedeploy your app to start using PostgreSQL!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"ERROR: Failed to connect to PostgreSQL")
        print(f"Details: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure DATABASE_URL is set correctly in Railway")
        print("2. Check that PostgreSQL service is running")
        print("3. Verify connection string format")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
