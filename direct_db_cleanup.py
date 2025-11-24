import os
import psycopg2

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

print(f"Connecting to: {db_url[:50]}...")
conn = psycopg2.connect(db_url)
cur = conn.cursor()

try:
    # First check what's in there
    print("\n=== CURRENT WATCHLIST ===")
    cur.execute("SELECT id, symbol, name FROM watchlist ORDER BY id DESC")
    rows = cur.fetchall()
    print(f"Total items: {len(rows)}")
    for row in rows:
        print(f"  ID: {row[0]}, Symbol: {row[1]}, Name: {row[2]}")
    
    # Delete RELIANCE entries
    print("\n=== DELETING RELIANCE ===")
    cur.execute("DELETE FROM watchlist WHERE LOWER(symbol) LIKE LOWER(%s)", ('%reliance%',))
    deleted = cur.rowcount
    print(f"Deleted: {deleted} rows")
    
    # Verify
    print("\n=== AFTER CLEANUP ===")
    cur.execute("SELECT id, symbol, name FROM watchlist ORDER BY id DESC")
    rows = cur.fetchall()
    print(f"Total items: {len(rows)}")
    for row in rows:
        print(f"  ID: {row[0]}, Symbol: {row[1]}, Name: {row[2]}")
    
    conn.commit()
    print("\nCleaned up successfully!")
finally:
    cur.close()
    conn.close()
