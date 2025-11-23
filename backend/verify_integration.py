"""
Integration verification script

FOLLOW: TheTool.prompt.md Section 9 (Testing Layers & Coverage Goals)
Uses centralized constants from backend/constants.py for URL configuration.
"""
import requests
import json
import time
from database import get_db_connection
from constants import get_api_base_url, API_URLS

print("1. Adding stock to watchlist...")
response = requests.post(f'{get_api_base_url()}{API_URLS.WATCHLIST}', 
    json={'symbol': 'INFY.NS', 'name': 'Infosys Limited'},
    timeout=10)
print(f"   Status: {response.status_code}")

print("\n2. Getting watchlist...")
response = requests.get(f'{get_api_base_url()}{API_URLS.WATCHLIST}')
print(f"   Stocks in watchlist: {len(response.json())}")
print(f"   Symbols: {[s['symbol'] for s in response.json()]}")

print("\n3. Running analysis on INFY.NS...")
response = requests.post(f'{get_api_base_url()}{API_URLS.ANALYZE}', 
    json={'tickers': ['INFY.NS'], 'capital': 100000},
    timeout=30)

job_id = response.json()['job_id']
print(f"   Job ID: {job_id}")

# Wait for completion
for i in range(30):
    status_response = requests.get(f'{get_api_base_url()}{API_URLS.get_status(job_id)}')
    status = status_response.json()
    
    if status['status'] == 'completed':
        print(f"   ✓ Analysis completed!")
        break
    print(f"   Waiting... ({i+1}/30)")
    time.sleep(1)

print("\n4. Fetching analysis history for INFY.NS...")
response = requests.get(f'{get_api_base_url()}{API_URLS.get_history("INFY.NS")}')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if data['history']:
        latest = data['history'][0]
        print(f"   ✓ Found analysis!")
        print(f"   - Verdict: {latest['verdict']}")
        print(f"   - Score: {latest['score']}")
        print(f"   - Entry: {latest['entry']}")
        print(f"   - Stop Loss: {latest['stop']}")
        print(f"   - Target: {latest['target']}")
    else:
        print(f"   ✗ No history found")
else:
    print(f"   Error: {response.json()}")

print("\n✓ Test complete!")
