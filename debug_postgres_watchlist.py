"""Debug script to check PostgreSQL watchlist directly"""
import os
import psycopg2
import subprocess

# Get database URL from Railway
try:
    result = subprocess.run(
        ['railway', 'run', 'python', '-c', 'import os; print(os.getenv("DATABASE_URL", ""))'],
        capture_output=True,
        text=True
    )
    db_url = result.stdout.strip()
except:
    db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("ERROR: Could not get DATABASE_URL")
    exit(1)

print(f"Connecting to database...")

# Connect directly to PostgreSQL
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

try:
    # Check watchlist contents
    print("\n=== WATCHLIST TABLE CONTENTS ===")
    cursor.execute("SELECT id, symbol, name, created_at FROM watchlist ORDER BY created_at DESC")
    rows = cursor.fetchall()
    print(f"Total rows: {len(rows)}")
    
    for row in rows:
        print(f"ID: {row[0]}, Symbol: {row[1]}, Name: {row[2]}, Created: {row[3]}")
    
    # Check for RELIANCE specifically
    print("\n=== CHECKING FOR RELIANCE ===")
    cursor.execute(
        "SELECT id, symbol, name, created_at FROM watchlist WHERE LOWER(symbol) LIKE LOWER(%s)",
        ('%reliance%',)
    )
    reliance_rows = cursor.fetchall()
    print(f"Reliance items found: {len(reliance_rows)}")
    for row in reliance_rows:
        print(f"  ID: {row[0]}, Symbol: {row[1]}, Name: {row[2]}, Created: {row[3]}")
        
finally:
    cursor.close()
    conn.close()
