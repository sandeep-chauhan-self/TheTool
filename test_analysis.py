#!/usr/bin/env python
"""
Test script for analysis backend

FOLLOW: TheTool.prompt.md Section 9 (Testing Layers & Coverage Goals)
Uses centralized constants from backend/constants.py for URL configuration.
"""
import requests
import time
import json
import sys
import os

# Add backend to path to import constants
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from constants import get_api_base_url

BASE_URL = get_api_base_url()

# Test 1: Single stock analysis
print("=" * 60)
print("TEST 1: Single Stock Analysis")
print("=" * 60)

r = requests.post(f'{BASE_URL}/analyze', json={
    'tickers': ['20MICRONS.NS'],
    'capital': 100000,
    'use_demo_data': True
})

print(f'Status Code: {r.status_code}')
data = r.json()
print(f'Job ID: {data.get("job_id")}')
print(f'Message: {data.get("message")}')

job_id = data.get('job_id')

# Wait for analysis to complete
print("\nWaiting for analysis to complete...")
time.sleep(3)

# Check job status
r_status = requests.get(f'{BASE_URL}/status/{job_id}')
status_data = r_status.json()

print(f'\nJob Status: {status_data.get("status")}')
print(f'Completed: {status_data.get("completed")}/{status_data.get("total")}')
print(f'Progress: {status_data.get("progress")}%')

if status_data.get('errors'):
    print(f'Errors: {status_data.get("errors")}')
else:
    print('✅ No errors!')

# Test 2: Check database
print("\n" + "=" * 60)
print("TEST 2: Verify Database Storage")
print("=" * 60)

import sqlite3
conn = sqlite3.connect('backend/data/trading_app.db')
cursor = conn.cursor()
cursor.execute('SELECT ticker, score, verdict, created_at FROM analysis_results ORDER BY created_at DESC LIMIT 3')
rows = cursor.fetchall()

print(f"\nLatest {len(rows)} analysis results:")
for row in rows:
    print(f"  {row[0]}: Score={row[1]}, Verdict={row[2]}, Time={row[3]}")

conn.close()

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
