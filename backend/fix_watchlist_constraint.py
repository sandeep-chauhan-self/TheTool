"""
Fix watchlist table constraint to allow same stock in multiple collections.

The old constraint was: UNIQUE(ticker) - only allows each ticker once globally
The new constraint is: UNIQUE(ticker, collection_id) - allows same ticker in different collections

Run this script to fix the constraint:
    python fix_watchlist_constraint.py
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from utils.logger import setup_logger

logger = setup_logger()

def fix_constraint():
    """Drop old unique constraint and create new composite one"""
    
    with get_db_session() as (conn, cursor):
        try:
            # List all constraints on watchlist table
            cursor.execute("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conrelid = 'watchlist'::regclass
            """)
            constraints = cursor.fetchall()
            print(f"Current constraints on watchlist table: {constraints}")
            
            # Drop all unique constraints on ticker alone
            drop_statements = [
                "ALTER TABLE watchlist DROP CONSTRAINT IF EXISTS watchlist_symbol_key",
                "ALTER TABLE watchlist DROP CONSTRAINT IF EXISTS watchlist_ticker_key",
                "ALTER TABLE watchlist DROP CONSTRAINT IF EXISTS watchlist_ticker_unique",
                "DROP INDEX IF EXISTS watchlist_ticker_idx",
                "DROP INDEX IF EXISTS watchlist_symbol_idx",
            ]
            
            for stmt in drop_statements:
                try:
                    cursor.execute(stmt)
                    print(f"Executed: {stmt}")
                except Exception as e:
                    print(f"Skipped (may not exist): {stmt} - {e}")
            
            conn.commit()
            
            # Check if composite index already exists
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'watchlist' AND indexname = 'watchlist_ticker_collection_idx'
            """)
            existing_idx = cursor.fetchone()
            
            if existing_idx:
                print("Dropping existing composite index to recreate...")
                cursor.execute("DROP INDEX IF EXISTS watchlist_ticker_collection_idx")
                conn.commit()
            
            # Create new composite unique index
            # Using COALESCE to handle NULL collection_id (Default collection)
            cursor.execute("""
                CREATE UNIQUE INDEX watchlist_ticker_collection_idx 
                ON watchlist(LOWER(ticker), COALESCE(collection_id, -1))
            """)
            conn.commit()
            print("Created new composite unique index: watchlist_ticker_collection_idx")
            
            # Verify
            cursor.execute("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conrelid = 'watchlist'::regclass
            """)
            final_constraints = cursor.fetchall()
            print(f"Final constraints on watchlist table: {final_constraints}")
            
            cursor.execute("""
                SELECT indexname FROM pg_indexes WHERE tablename = 'watchlist'
            """)
            final_indexes = cursor.fetchall()
            print(f"Final indexes on watchlist table: {final_indexes}")
            
            print("\n✅ Migration completed successfully!")
            print("You can now add the same stock to multiple watchlists.")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing watchlist constraint for multiple collections support")
    print("=" * 60)
    fix_constraint()
