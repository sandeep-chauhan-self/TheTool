"""
Migrate database timestamps to IST (Indian Standard Time)

This script converts all existing timestamps in the database to IST.
Existing timestamps are assumed to be in UTC or system timezone and will be shifted to IST.

Usage:
    python migrate_to_ist.py
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta
from config import config
from database import get_db_connection, DATABASE_TYPE
import psycopg2

# Indian Standard Time offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def convert_timestamp_to_ist(ts_str):
    """
    Convert a timestamp string to IST ISO format.
    Assumes input is in UTC or naive (system time).
    """
    if not ts_str:
        return None
    
    try:
        # Try to parse ISO format
        if '+' in ts_str or ts_str.endswith('Z'):
            # Already has timezone info
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        else:
            # Naive datetime - assume UTC
            dt = datetime.fromisoformat(ts_str)
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to IST
        ist_dt = dt.astimezone(IST)
        return ist_dt.isoformat()
    except Exception as e:
        print(f"Error converting timestamp '{ts_str}': {e}")
        return ts_str


def migrate_sqlite():
    """Migrate SQLite database timestamps to IST"""
    print("Migrating SQLite database to IST...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables_to_update = [
        ('analysis_results', ['created_at', 'updated_at']),
        ('analysis_jobs', ['created_at', 'updated_at', 'started_at', 'completed_at']),
        ('watchlist', ['created_at', 'last_analyzed_at']),
        ('api_keys', ['created_at', 'revoked_at', 'last_used_at']),
        ('api_key_audit', ['created_at']),
    ]
    
    for table_name, timestamp_cols in tables_to_update:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"  Table {table_name} does not exist, skipping...")
            continue
        
        for col in timestamp_cols:
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            col_names = [row[1] for row in cursor.fetchall()]
            if col not in col_names:
                continue
            
            print(f"  Updating {table_name}.{col}...")
            
            # Get all rows with this column
            cursor.execute(f"SELECT rowid, {col} FROM {table_name}")
            rows = cursor.fetchall()
            
            # Update each timestamp
            for rowid, ts_str in rows:
                if ts_str:
                    new_ts = convert_timestamp_to_ist(ts_str)
                    if new_ts != ts_str:
                        cursor.execute(f"UPDATE {table_name} SET {col} = ? WHERE rowid = ?", (new_ts, rowid))
            
            conn.commit()
            print(f"    ✓ Updated {len(rows)} timestamps")
    
    conn.close()
    print("SQLite migration complete!")


def migrate_postgres():
    """Migrate PostgreSQL database timestamps to IST"""
    print("Migrating PostgreSQL database to IST...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables_to_update = [
        ('analysis_results', ['created_at', 'updated_at']),
        ('analysis_jobs', ['created_at', 'updated_at', 'started_at', 'completed_at']),
        ('watchlist', ['created_at', 'last_analyzed_at']),
        ('api_keys', ['created_at', 'revoked_at', 'last_used_at']),
        ('api_key_audit', ['created_at']),
    ]
    
    for table_name, timestamp_cols in tables_to_update:
        # Check if table exists
        cursor.execute(f"""
            SELECT EXISTS(
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        
        if not cursor.fetchone()[0]:
            print(f"  Table {table_name} does not exist, skipping...")
            continue
        
        for col in timestamp_cols:
            # Check if column exists
            cursor.execute(f"""
                SELECT EXISTS(
                    SELECT FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                )
            """, (table_name, col))
            
            if not cursor.fetchone()[0]:
                continue
            
            print(f"  Updating {table_name}.{col}...")
            
            # Get all rows with this column
            cursor.execute(f"SELECT id, {col} FROM {table_name}")
            rows = cursor.fetchall()
            
            # Update each timestamp
            for row_id, ts_str in rows:
                if ts_str:
                    new_ts = convert_timestamp_to_ist(str(ts_str))
                    if new_ts != str(ts_str):
                        cursor.execute(f"UPDATE {table_name} SET {col} = %s WHERE id = %s", (new_ts, row_id))
            
            conn.commit()
            print(f"    ✓ Updated {len(rows)} timestamps")
    
    cursor.close()
    conn.close()
    print("PostgreSQL migration complete!")


if __name__ == "__main__":
    try:
        if DATABASE_TYPE == 'postgres':
            migrate_postgres()
        else:
            migrate_sqlite()
        
        print("\n✓ Timestamp migration complete!")
        print("  All timestamps are now in Indian Standard Time (IST)")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
