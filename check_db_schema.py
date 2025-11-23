import sqlite3
import os

db_path = 'backend/data/stocks.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check watchlist columns
    cursor.execute('PRAGMA table_info(watchlist)')
    print('=== WATCHLIST columns ===')
    for col in cursor.fetchall():
        print(f'  {col[1]} ({col[2]})')
    
    # Check analysis_results columns
    cursor.execute('PRAGMA table_info(analysis_results)')
    print('\n=== ANALYSIS_RESULTS columns ===')
    for col in cursor.fetchall():
        print(f'  {col[1]} ({col[2]})')
    
    # Check if analysis_jobs_details exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_jobs_details'")
    if cursor.fetchone():
        print('\n✅ analysis_jobs_details table EXISTS')
        cursor.execute('PRAGMA table_info(analysis_jobs_details)')
        print('=== ANALYSIS_JOBS_DETAILS columns ===')
        for col in cursor.fetchall():
            print(f'  {col[1]} ({col[2]})')
    else:
        print('\n❌ analysis_jobs_details table MISSING')
    
    # Check if analysis_raw_data exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_raw_data'")
    if cursor.fetchone():
        print('\n✅ analysis_raw_data table EXISTS')
        cursor.execute('PRAGMA table_info(analysis_raw_data)')
        print('=== ANALYSIS_RAW_DATA columns ===')
        for col in cursor.fetchall():
            print(f'  {col[1]} ({col[2]})')
    else:
        print('\n❌ analysis_raw_data table MISSING')
    
    # Check indices
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name")
    print('\n=== Indices ===')
    indices = cursor.fetchall()
    if indices:
        for idx in indices:
            print(f'  {idx[0]}')
    else:
        print('  (none)')
    
    conn.close()
else:
    print('Database not found at', db_path)
