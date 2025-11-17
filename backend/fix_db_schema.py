"""Fix database schema - add missing entry_method column"""
import sqlite3
import os

DB_PATH = os.path.join('data', 'trading_app.db')

if os.path.exists(DB_PATH):
    print(f"Fixing database schema: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check analysis_results table
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # Add entry_method column if missing
    if 'entry_method' not in columns:
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN entry_method TEXT DEFAULT 'unknown'")
            conn.commit()
            print("? Added 'entry_method' column")
        except Exception as e:
            print(f"? Error adding entry_method: {e}")
    else:
        print("* 'entry_method' column already exists")
    
    # Add data_source column if missing
    if 'data_source' not in columns:
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN data_source TEXT DEFAULT 'demo'")
            conn.commit()
            print("? Added 'data_source' column")
        except Exception as e:
            print(f"? Error adding data_source: {e}")
    else:
        print("* 'data_source' column already exists")
    
    # Add is_demo_data column if missing
    if 'is_demo_data' not in columns:
        try:
            cursor.execute("ALTER TABLE analysis_results ADD COLUMN is_demo_data INTEGER DEFAULT 1")
            conn.commit()
            print("? Added 'is_demo_data' column")
        except Exception as e:
            print(f"? Error adding is_demo_data: {e}")
    else:
        print("* 'is_demo_data' column already exists")
    
    conn.close()
    print("\nSchema fix complete!")
else:
    print(f"Database not found at: {DB_PATH}")
