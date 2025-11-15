import requests

print('Checking analysis results for all stocks...')
for ticker in ['21STCENMGM.NS', 'INFY.NS']:
    response = requests.get(f'http://localhost:5000/history/{ticker}')
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
