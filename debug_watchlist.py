"""Debug script to check watchlist database contents"""
import sys
sys.path.insert(0, 'backend')

from app import create_app
from database import query_db

app = create_app()

with app.app_context():
    # Check all watchlist items
    print("=== ALL WATCHLIST ITEMS ===")
    items = query_db("SELECT id, symbol, name, created_at FROM watchlist ORDER BY created_at DESC")
    items = query_db("SELECT id, symbol, name, created_at FROM watchlist ORDER BY created_at DESC")
    print(f"Total items: {len(items)}")
    
    for idx, item in enumerate(items):
        print(f"{idx + 1}. {item}")
        if isinstance(item, (tuple, list)):
            print(f"   ID: {item[0]}, Symbol: {item[1]}, Name: {item[2]}, Created: {item[3]}")
        else:
            print(f"   {dict(item)}")
    
    # Check specifically for RELIANCE
    print("\n=== CHECKING FOR RELIANCE ===")
    reliance = query_db(
        "SELECT id, symbol, name, created_at FROM watchlist WHERE LOWER(symbol) LIKE LOWER(?)",
        ('%reliance%',)
    )
    print(f"Reliance items found: {len(reliance)}")
    for item in reliance:
        print(f"  {item}")
