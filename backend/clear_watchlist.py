#!/usr/bin/env python
"""
Clear the watchlist table to start fresh.
Users should manually add stocks they want to track via the UI.
"""
from database import get_db_connection

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear watchlist
        cursor.execute("DELETE FROM watchlist")
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM watchlist")
        count = cursor.fetchone()[0]
        
        print(f"✓ Watchlist cleared successfully. Current count: {count}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"✗ Error clearing watchlist: {e}")
        exit(1)
