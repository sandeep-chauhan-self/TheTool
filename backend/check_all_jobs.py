#!/usr/bin/env python3
"""Check all jobs"""
import sqlite3
import json

conn = sqlite3.connect('./data/trading_app.db')
cursor = conn.cursor()

# Get ALL jobs
cursor.execute('''
SELECT job_id, status, total, completed, successful, errors 
FROM analysis_jobs 
ORDER BY created_at DESC 
LIMIT 10
''')
jobs = cursor.fetchall()
print('All Analysis Jobs:')
for job in jobs:
    job_id, status, total, completed, successful, errors_json = job
    try:
        errors = json.loads(errors_json) if errors_json else []
        error_count = len(errors)
        sample_errors = [e if isinstance(e, str) else (e.get('error', str(e))[:80]) for e in errors[:3]]
    except Exception as e:
        error_count = 0
        sample_errors = []
    
    print(f'\n  Job: {job_id[:20]}... | Status: {status:12} | {completed:4}/{total:4} | Successful: {successful:3}')
    if error_count > 0:
        print(f'    Errors ({error_count}): {sample_errors}')

conn.close()
