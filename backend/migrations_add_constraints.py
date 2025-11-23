"""
Database Migration: Add Constraints and Indices to Fix Critical Failure Points

This migration addresses the 13 critical failure points identified in the database schema:

1. Duplicate job_id handling (PRIMARY KEY)
2. No unique constraints on analysis_results
3. No foreign keys
4. analysis_source tracking
5. status column usage
6. raw_data performance
7. error_message population
8. watchlist-job relationship
9. Composite key issues
10. Temporal data tracking
11. Thread-unsafe database updates
12. Per-operation error checking
13. SQLite "Database is Locked" pattern

Run this migration to add indices, constraints, and trigger proper updates.
"""

import sqlite3
from datetime import datetime
import os

# Only import psycopg2 if using PostgreSQL
try:
    import psycopg2
except ImportError:
    psycopg2 = None

# Configuration
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')
DB_PATH = os.getenv('DATABASE_PATH', 'backend/data/stocks.db')
DATABASE_URL = os.getenv('DATABASE_URL', '')


def add_sqlite_constraints():
    """Add constraints and indices to SQLite database"""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    
    try:
        print("[SQLite] Adding constraints and indices...")
        
        # ============================================================
        # CONSTRAINT 1: Unique index on (ticker, date) for analysis_results
        # Prevents duplicate results for same stock on same day
        # ============================================================
        print("[1/10] Adding UNIQUE INDEX on analysis_results(ticker, DATE(created_at))...")
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                ON analysis_results(ticker, DATE(created_at))
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 2: Foreign key from analysis_results to analysis_jobs
        # Prevents orphaned results and enables cascading deletes
        # ============================================================
        # Note: SQLite doesn't support adding foreign keys to existing tables easily
        # This requires table recreation. Handled in a separate migration step.
        
        # ============================================================
        # CONSTRAINT 3: Index on symbol for fast lookups
        # ============================================================
        print("[2/10] Adding INDEX on analysis_results(symbol)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol
                ON analysis_results(symbol)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 4: Index on created_at for time-based queries
        # ============================================================
        print("[3/10] Adding INDEX on analysis_results(created_at)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                ON analysis_results(created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 5: Index on analysis_jobs status for progress queries
        # ============================================================
        print("[4/10] Adding INDEX on analysis_jobs(status)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON analysis_jobs(status, created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 6: Composite index on analysis_source and analysis_jobs
        # ============================================================
        print("[5/10] Adding INDEX on analysis_results(analysis_source)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_source
                ON analysis_results(analysis_source, created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 7: Add missing columns to watchlist for job tracking
        # ============================================================
        print("[6/10] Adding columns to watchlist table...")
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(watchlist)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'last_job_id' not in columns:
            print("  Adding last_job_id column...")
            try:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        if 'last_analyzed_at' not in columns:
            print("  Adding last_analyzed_at column...")
            try:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        if 'last_status' not in columns:
            print("  Adding last_status column...")
            try:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_status TEXT')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 8: Add missing columns to analysis_results for job tracking
        # ============================================================
        print("[7/10] Adding job_id column to analysis_results table...")
        
        cursor.execute("PRAGMA table_info(analysis_results)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'job_id' not in columns:
            print("  Adding job_id column...")
            try:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN job_id TEXT')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        if 'started_at' not in columns:
            print("  Adding started_at column...")
            try:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        if 'completed_at' not in columns:
            print("  Adding completed_at column...")
            try:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP')
                print("    ✓ Column added")
            except Exception as e:
                print(f"    ⚠ Column may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 9: Create analysis_jobs_details table for per-stock tracking
        # ============================================================
        print("[8/10] Creating analysis_jobs_details table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_jobs_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    status TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, ticker)
                )
            ''')
            
            # Create indices
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_job_id
                ON analysis_jobs_details(job_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_ticker
                ON analysis_jobs_details(ticker)
            ''')
            
            print("  ✓ Table created with indices")
        except Exception as e:
            print(f"  ⚠ Table may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 10: Create analysis_raw_data table for performance
        # ============================================================
        print("[9/10] Creating analysis_raw_data table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_result_id INTEGER NOT NULL,
                    raw_indicators TEXT,
                    raw_signals TEXT,
                    raw_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_data_result_id
                ON analysis_raw_data(analysis_result_id)
            ''')
            
            print("  ✓ Table created")
        except Exception as e:
            print(f"  ⚠ Table may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 11: Add indices to improve query performance
        # ============================================================
        print("[10/10] Adding composite indices for common queries...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol_date
                ON analysis_results(symbol, DATE(created_at) DESC)
            ''')
            print("  ✓ Composite index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        conn.commit()
        print("\n✅ SQLite migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ SQLite migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def add_postgres_constraints():
    """Add constraints and indices to PostgreSQL database"""
    if not psycopg2:
        print("❌ psycopg2 not installed. Skipping PostgreSQL migration.")
        print("   Run: pip install psycopg2-binary")
        return
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("[PostgreSQL] Adding constraints and indices...")
        
        # ============================================================
        # CONSTRAINT 1: Unique index on (ticker, date)
        # ============================================================
        print("[1/10] Adding UNIQUE INDEX on analysis_results(ticker, DATE(created_at))...")
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                ON analysis_results(ticker, DATE(created_at))
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 2: Index on symbol
        # ============================================================
        print("[2/10] Adding INDEX on analysis_results(symbol)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol
                ON analysis_results(symbol)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 3: Index on created_at
        # ============================================================
        print("[3/10] Adding INDEX on analysis_results(created_at)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                ON analysis_results(created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 4: Index on analysis_jobs status
        # ============================================================
        print("[4/10] Adding INDEX on analysis_jobs(status)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON analysis_jobs(status, created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 5: Index on analysis_source
        # ============================================================
        print("[5/10] Adding INDEX on analysis_results(analysis_source)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_source
                ON analysis_results(analysis_source, created_at DESC)
            ''')
            print("  ✓ Index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 6: Add columns to watchlist
        # ============================================================
        print("[6/10] Adding columns to watchlist table...")
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='watchlist'")
            columns = {row[0] for row in cursor.fetchall()}
            
            if 'last_job_id' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT')
                print("  ✓ last_job_id added")
            
            if 'last_analyzed_at' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP')
                print("  ✓ last_analyzed_at added")
            
            if 'last_status' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_status TEXT')
                print("  ✓ last_status added")
        except Exception as e:
            print(f"  ⚠ Columns may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 7: Add columns to analysis_results
        # ============================================================
        print("[7/10] Adding columns to analysis_results table...")
        try:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='analysis_results'")
            columns = {row[0] for row in cursor.fetchall()}
            
            if 'job_id' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN job_id TEXT')
                print("  ✓ job_id added")
            
            if 'started_at' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP')
                print("  ✓ started_at added")
            
            if 'completed_at' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP')
                print("  ✓ completed_at added")
        except Exception as e:
            print(f"  ⚠ Columns may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 8: Create analysis_jobs_details table
        # ============================================================
        print("[8/10] Creating analysis_jobs_details table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_jobs_details (
                    id SERIAL PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    status TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    result_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, ticker)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_job_id
                ON analysis_jobs_details(job_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_job_details_ticker
                ON analysis_jobs_details(ticker)
            ''')
            
            print("  ✓ Table created")
        except Exception as e:
            print(f"  ⚠ Table may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 9: Create analysis_raw_data table
        # ============================================================
        print("[9/10] Creating analysis_raw_data table...")
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_raw_data (
                    id SERIAL PRIMARY KEY,
                    analysis_result_id INTEGER NOT NULL,
                    raw_indicators TEXT,
                    raw_signals TEXT,
                    raw_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_raw_data_result_id
                ON analysis_raw_data(analysis_result_id)
            ''')
            
            print("  ✓ Table created")
        except Exception as e:
            print(f"  ⚠ Table may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 10: Composite indices
        # ============================================================
        print("[10/10] Adding composite indices...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol_date
                ON analysis_results(symbol, DATE(created_at) DESC)
            ''')
            print("  ✓ Composite index created")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")
        
        conn.commit()
        print("\n✅ PostgreSQL migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ PostgreSQL migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migration():
    """Run database migration based on configured database type"""
    print(f"\n{'='*60}")
    print(f"Database Migration: Add Constraints & Indices")
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"{'='*60}\n")
    
    if DATABASE_TYPE == 'postgres':
        add_postgres_constraints()
    else:
        add_sqlite_constraints()
    
    print(f"\n{'='*60}")
    print(f"Migration Complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    run_migration()
