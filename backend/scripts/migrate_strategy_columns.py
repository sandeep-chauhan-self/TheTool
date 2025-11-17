"""
Database schema migration: Add strategy columns to all_stocks_analysis table
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'trading_app.db')

def migrate_add_strategy_columns():
    """Add strategy-related columns to all_stocks_analysis table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(all_stocks_analysis)")
        columns = [row[1] for row in cursor.fetchall()]
        
        columns_to_add = [
            ('strategy_recommendation', 'TEXT'),
            ('strategy_entry_price', 'REAL'),
            ('strategy_stop_loss', 'REAL'),
            ('strategy_target_price', 'REAL'),
            ('strategy_confidence', 'REAL')
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                cursor.execute(f'ALTER TABLE all_stocks_analysis ADD COLUMN {col_name} {col_type}')
                print(f"? Added column: {col_name}")
            else:
                print(f"- Column already exists: {col_name}")
        
        conn.commit()
        conn.close()
        print("\n? Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n? Migration failed: {e}")
        return False

if __name__ == '__main__':
    migrate_add_strategy_columns()
