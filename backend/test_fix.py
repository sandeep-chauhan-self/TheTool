"""
Quick test for single stock analysis

FOLLOW: TheTool.prompt.md Section 9 (Testing Layers & Coverage Goals)
Uses centralized constants from backend/constants.py for URL configuration.
"""
import requests
import json
import time
from database import get_db_connection
from constants import get_api_base_url, API_URLS

BASE_URL = get_api_base_url()

# Test single stock analysis
print("Sending analysis request...")
response = requests.post(f'{BASE_URL}{API_URLS.ANALYZE}', 
    json={'tickers': ['RELIANCE.NS'], 'capital': 100000},
    timeout=30)

print('Response:', response.status_code)
print(json.dumps(response.json(), indent=2))

job_id = response.json()['job_id']
print(f'\nJob ID: {job_id}')

# Wait for job to complete
print("\nWaiting for analysis to complete...")
for i in range(30):
    status_response = requests.get(f'{BASE_URL}{API_URLS.get_status(job_id)}')
    status = status_response.json()
    print(f'Check {i+1}: {status["status"]} - {status["completed"]}/{status["total"]} completed')
    
    if status['status'] == 'completed':
        print('\n✓ Job completed!')
        print('Errors:', status.get('errors'))
        break
    time.sleep(1)

# Now check if result is in database
print('\n--- Checking Database ---')
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM analysis_results WHERE ticker = "RELIANCE.NS"')
count = cursor.fetchone()[0]
print(f'Records in database for RELIANCE.NS: {count}')

if count > 0:
    cursor.execute('SELECT ticker, score, verdict, entry, stop_loss, target FROM analysis_results WHERE ticker = "RELIANCE.NS" ORDER BY created_at DESC LIMIT 1')
    result = cursor.fetchone()
    print(f'Latest result: Ticker={result[0]}, Score={result[1]}, Verdict={result[2]}, Entry={result[3]}, SL={result[4]}, Target={result[5]}')
else:
    print("✗ NO RESULTS IN DATABASE!")

conn.close()
