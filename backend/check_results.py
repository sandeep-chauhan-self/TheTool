"""
Check analysis results script

FOLLOW: TheTool.prompt.md Section 9 (Testing Layers & Coverage Goals)
Uses centralized constants from backend/constants.py for URL configuration.
"""
import requests
from constants import get_api_base_url, API_URLS

print('Checking analysis results for all stocks...')
for ticker in ['21STCENMGM.NS', 'INFY.NS']:
    response = requests.get(f'{get_api_base_url()}{API_URLS.get_history(ticker)}')
    if response.status_code == 200:
        data = response.json()
        if data['history']:
            result = data['history'][0]
            verdict = result.get('verdict', 'N/A')
            score = result.get('score', 'N/A')
            print(f'\n✓ {ticker}:')
            print(f'  Verdict: {verdict}')
            print(f'  Score: {score}%')
        else:
            print(f'\n✗ {ticker}: No analysis found')
    else:
        print(f'\n✗ {ticker}: Error - {response.status_code}')

print('\n\n--- Now refreshing browser should show results ---')
