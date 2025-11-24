"""Clean up duplicate/orphaned watchlist entries"""
import sys
sys.path.insert(0, 'backend')

from app import create_app
from database import execute_db, query_db

app = create_app()

with app.app_context():
    print("=== CHECKING WATCHLIST ===")
    items = query_db("SELECT id, symbol, name FROM watchlist")
    print(f"Total items: {len(items)}")
    for idx, item in enumerate(items):
        print(f"{idx + 1}. {item}")
    
    # Delete RELIANCE if it exists
    print("\n=== DELETING RELIANCE ===")
    try:
        deleted_count = execute_db(
            "DELETE FROM watchlist WHERE LOWER(symbol) LIKE LOWER(?)",
            ('%reliance%',)
        )
        print(f"Deleted {deleted_count} items")
    except Exception as e:
        print(f"Error: {e}")
    
    # Verify
    print("\n=== VERIFICATION ===")
    items = query_db("SELECT id, symbol, name FROM watchlist")
    print(f"Total items after cleanup: {len(items)}")
    for idx, item in enumerate(items):
        print(f"{idx + 1}. {item}")
