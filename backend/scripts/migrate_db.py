"""Database migration script to add missing columns"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'trading_app.db')

if os.path.exists(DB_PATH):
    print(f"Migrating database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(analysis_jobs)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add started_at if missing
    if 'started_at' not in columns:
        try:
            cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN started_at TIMESTAMP")
            conn.commit()
            print("+ Added 'started_at' column")
        except Exception as e:
            print(f"- Error adding started_at: {e}")
    else:
        print("* 'started_at' column already exists")
    
    # Add successful if missing
    if 'successful' not in columns:
        try:
            cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN successful INTEGER DEFAULT 0")
            conn.commit()
            print("+ Added 'successful' column")
        except Exception as e:
            print(f"- Error adding successful: {e}")
    else:
        print("* 'successful' column already exists")
    
    conn.close()
    print("\nMigration complete!")
else:
    print(f"Database not found at: {DB_PATH}")
    print("It will be created on first run")
