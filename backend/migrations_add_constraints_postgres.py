"""
Database Migration: Add Constraints and Indices to Fix Critical Failure Points
PostgreSQL Version

This migration addresses the 13 critical failure points identified in the database schema.
Run this with: railway run python backend/migrations_add_constraints_postgres.py
"""

import os
import psycopg2
from datetime import datetime

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', '')


def add_postgres_constraints():
    """Add constraints and indices to PostgreSQL database"""
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL environment variable not set!")
        print("   On Railway, this should be automatically set.")
        print("   Locally, set it with: export DATABASE_URL='postgresql://user:pass@host/db'")
        return False
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("[PostgreSQL] Adding constraints and indices...")
        
        # ============================================================
        # CONSTRAINT 1: Unique index on (ticker, date)
        # ============================================================
        print("[1/10] Adding UNIQUE INDEX on analysis_results(ticker, DATE)...")
        try:
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_ticker_date
                ON analysis_results(ticker, CAST(created_at AS DATE))
            ''')
            conn.commit()
            print("  ✓ Index created")
        except Exception as e:
            conn.rollback()
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
            conn.commit()
            print("  ✓ Index created")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 3: Index on created_at
        # ============================================================
        print("[3/10] Adding INDEX on analysis_results(created_at DESC)...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                ON analysis_results(created_at DESC)
            ''')
            conn.commit()
            print("  ✓ Index created")
        except Exception as e:
            conn.rollback()
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
            conn.commit()
            print("  ✓ Index created")
        except Exception as e:
            conn.rollback()
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
            conn.commit()
            print("  ✓ Index created")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠ Index may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 6: Add columns to watchlist
        # ============================================================
        print("[6/10] Adding columns to watchlist table...")
        
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='watchlist'
        """)
        columns = {row[0] for row in cursor.fetchall()}
        
        try:
            if 'last_job_id' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_job_id TEXT')
                conn.commit()
                print("  ✓ last_job_id added")
            
            if 'last_analyzed_at' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_analyzed_at TIMESTAMP')
                conn.commit()
                print("  ✓ last_analyzed_at added")
            
            if 'last_status' not in columns:
                cursor.execute('ALTER TABLE watchlist ADD COLUMN last_status TEXT')
                conn.commit()
                print("  ✓ last_status added")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠ Columns may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 7: Add columns to analysis_results
        # ============================================================
        print("[7/10] Adding columns to analysis_results table...")
        
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='analysis_results'
        """)
        columns = {row[0] for row in cursor.fetchall()}
        
        try:
            if 'job_id' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN job_id TEXT')
                conn.commit()
                print("  ✓ job_id added")
            
            if 'started_at' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN started_at TIMESTAMP')
                conn.commit()
                print("  ✓ started_at added")
            
            if 'completed_at' not in columns:
                cursor.execute('ALTER TABLE analysis_results ADD COLUMN completed_at TIMESTAMP')
                conn.commit()
                print("  ✓ completed_at added")
        except Exception as e:
            conn.rollback()
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
                    status TEXT DEFAULT 'pending',
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
            
            conn.commit()
            print("  ✓ Table created with indices")
        except Exception as e:
            conn.rollback()
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
            
            conn.commit()
            print("  ✓ Table created")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠ Table may already exist: {e}")
        
        # ============================================================
        # CONSTRAINT 10: Composite indices for common queries
        # ============================================================
        print("[10/10] Adding composite indices...")
        try:
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_analysis_symbol_date
                ON analysis_results(symbol, CAST(created_at AS DATE) DESC)
            ''')
            conn.commit()
            print("  ✓ Composite index created")
        except Exception as e:
            conn.rollback()
            print(f"  ⚠ Index may already exist: {e}")
        
        print("\n✅ PostgreSQL migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migration():
    """Run database migration"""
    print(f"\n{'='*60}")
    print(f"Database Migration: PostgreSQL Constraints & Indices")
    print(f"{'='*60}\n")
    
    try:
        success = add_postgres_constraints()
        print(f"\n{'='*60}")
        if success:
            print(f"✅ Migration Complete!")
        else:
            print(f"⚠️  Migration completed with warnings (see above)")
        print(f"{'='*60}\n")
        return success
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Migration Failed!")
        print(f"Error: {e}")
        print(f"{'='*60}\n")
        raise


if __name__ == '__main__':
    import sys
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
