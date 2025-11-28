#!/usr/bin/env python3
"""Check analysis results and errors"""
import sqlite3

conn = sqlite3.connect('./data/trading_app.db')
cursor = conn.cursor()

# Get all records count
cursor.execute('SELECT COUNT(*) FROM analysis_results')
total = cursor.fetchone()[0]
print(f'Total records in analysis_results: {total}')

# Get sample records
cursor.execute('''
SELECT ticker, symbol, verdict, score, status, error_message 
FROM analysis_results 
LIMIT 20
''')
records = cursor.fetchall()
print('\nSample Records:')
for rec in records:
    error_msg = str(rec[5])[:50] if rec[5] else 'None'
    print(f'  {str(rec[0]):20} | Verdict: {str(rec[2]):10} | Score: {str(rec[3]):8} | Status: {str(rec[4]):15}')

# Get count by status
cursor.execute('''
SELECT status, COUNT(*) 
FROM analysis_results 
GROUP BY status
''')
status_counts = cursor.fetchall()
print('\nRecords by Status:')
for status, count in status_counts:
    print(f'  {status}: {count}')

# Get recent errors
cursor.execute('''
SELECT ticker, error_message 
FROM analysis_results 
WHERE error_message IS NOT NULL 
LIMIT 10
''')
errors = cursor.fetchall()
print('\nRecent Errors:')
for ticker, error in errors:
    print(f'  {ticker}: {error[:80]}')

conn.close()
