#!/usr/bin/env python3
"""Check analysis jobs and error details"""
import sqlite3
import json

conn = sqlite3.connect('./data/trading_app.db')
cursor = conn.cursor()

# Get job details
cursor.execute('''
SELECT job_id, status, total, completed, successful, errors 
FROM analysis_jobs 
ORDER BY created_at DESC 
LIMIT 5
''')
jobs = cursor.fetchall()
print('Recent Analysis Jobs:')
for job in jobs:
    job_id, status, total, completed, successful, errors_json = job
    try:
        errors = json.loads(errors_json) if errors_json else []
        error_count = len(errors)
    except:
        error_count = 0
    
    print(f'\n  Job ID: {job_id}')
    print(f'    Status: {status}')
    print(f'    Progress: {completed}/{total}')
    print(f'    Successful: {successful}')
    print(f'    Errors: {error_count}')
    
    if errors:
        print(f'    Sample Errors:')
        for err in errors[:5]:
            if isinstance(err, dict):
                ticker = err.get('ticker', 'Unknown')
                error_msg = err.get('error', 'No message')[:80]
                print(f'      {ticker}: {error_msg}')

conn.close()
