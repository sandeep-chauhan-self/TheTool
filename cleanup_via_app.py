"""Cleanup via Flask app context - runs in Railway container environment"""
import sys
sys.path.insert(0, 'backend')

from app import create_app
from database import query_db, execute_db

app = create_app()

with app.app_context():
    print("=== CHECKING PRODUCTION WATCHLIST ===")
    items = query_db("SELECT id, symbol, name FROM watchlist ORDER BY id DESC")
    print(f"Total items before cleanup: {len(items)}")
    for idx, item in enumerate(items):
        if isinstance(item, (tuple, list)):
            print(f"  {idx + 1}. ID: {item[0]}, Symbol: {item[1]}, Name: {item[2]}")
        else:
            print(f"  {idx + 1}. {dict(item)}")
    
    print("\n=== DELETING ORPHANED/DUPLICATE ENTRIES ===")
    # Delete duplicates, keeping only the first (oldest) entry for each symbol
    deleted = execute_db("""
        DELETE FROM watchlist 
        WHERE id NOT IN (
            SELECT MIN(id) FROM watchlist GROUP BY LOWER(symbol)
        )
    """)
    print(f"Deleted: {deleted} duplicate entries")
    
    print("\n=== FINAL WATCHLIST ===")
    items = query_db("SELECT id, symbol, name FROM watchlist ORDER BY id DESC")
    print(f"Total items after cleanup: {len(items)}")
    for idx, item in enumerate(items):
        if isinstance(item, (tuple, list)):
            print(f"  {idx + 1}. ID: {item[0]}, Symbol: {item[1]}, Name: {item[2]}")
        else:
            print(f"  {idx + 1}. {dict(item)}")
    
    print("\nCleanup complete!")
