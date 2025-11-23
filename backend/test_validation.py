"""
Test ticker validation enhancements
"""
from utils.api_utils import RequestValidator, validate_request

def print_test_header(test_num, test_name):
    print('=' * 60)
    print(f'TEST {test_num}: {test_name}')
    print('=' * 60)

def print_result(passed, message):
    symbol = '✓' if passed else '✗'
    status = 'PASSED' if passed else 'FAILED'
    print(f'{symbol} {status} - {message}')

# Test 1: Empty ticker string
print_test_header(1, 'Empty ticker string')
request1 = {'tickers': [''], 'capital': 100000}
validated, error = validate_request(request1, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Empty ticker rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
    if error[0]['error'].get('details', {}).get('validation_errors'):
        for err in error[0]['error']['details']['validation_errors']:
            print(f'    - {err["message"]}')
else:
    print_result(False, 'Empty ticker should be rejected')
print()

# Test 2: Short ticker without exchange code
print_test_header(2, 'Short ticker without exchange code')
request2 = {'tickers': ['TCS'], 'capital': 100000}
validated, error = validate_request(request2, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Short ticker rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
    if error[0]['error'].get('details', {}).get('validation_errors'):
        for err in error[0]['error']['details']['validation_errors']:
            print(f'    - {err["message"]}')
else:
    print_result(False, 'Short ticker should be rejected')
print()

# Test 3: Duplicate tickers
print_test_header(3, 'Duplicate tickers')
request3 = {'tickers': ['TCS.NS', 'TCS.NS', 'INFY.NS'], 'capital': 100000}
validated, error = validate_request(request3, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Duplicate tickers rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
    if error[0]['error'].get('details', {}).get('validation_errors'):
        for err in error[0]['error']['details']['validation_errors']:
            print(f'    - {err["message"]}')
else:
    print_result(False, 'Duplicate tickers should be rejected')
print()

# Test 4: Valid tickers
print_test_header(4, 'Valid tickers')
request4 = {'tickers': ['TCS.NS', 'INFY.NS', 'RELIANCE.NS'], 'capital': 100000}
validated, error = validate_request(request4, RequestValidator.AnalyzeRequest)
if not error and validated:
    print_result(True, 'Valid tickers accepted')
    print(f'  Validated tickers: {validated["tickers"]}')
else:
    print_result(False, 'Valid tickers should be accepted')
    if error:
        print(f'  Error: {error[0]["error"]["message"]}')
print()

# Test 5: Whitespace-only ticker
print_test_header(5, 'Whitespace-only ticker')
request5 = {'tickers': ['   '], 'capital': 100000}
validated, error = validate_request(request5, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Whitespace ticker rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
    if error[0]['error'].get('details', {}).get('validation_errors'):
        for err in error[0]['error']['details']['validation_errors']:
            print(f'    - {err["message"]}')
else:
    print_result(False, 'Whitespace ticker should be rejected')
print()

# Test 6: Mixed valid and invalid tickers
print_test_header(6, 'Mixed valid and invalid tickers')
request6 = {'tickers': ['TCS.NS', 'INFY', 'RELIANCE.NS'], 'capital': 100000}
validated, error = validate_request(request6, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Mixed invalid tickers rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
    if error[0]['error'].get('details', {}).get('validation_errors'):
        for err in error[0]['error']['details']['validation_errors']:
            print(f'    - {err["message"]}')
else:
    print_result(False, 'Mixed invalid tickers should be rejected')
print()

# Test 7: Empty tickers list
print_test_header(7, 'Empty tickers list')
request7 = {'tickers': [], 'capital': 100000}
validated, error = validate_request(request7, RequestValidator.AnalyzeRequest)
if error:
    print_result(True, 'Empty list rejected')
    print(f'  Error message: {error[0]["error"]["message"]}')
else:
    print_result(False, 'Empty list should be rejected')
print()

# Test 8: Valid single ticker
print_test_header(8, 'Valid single ticker')
request8 = {'tickers': ['TCS.NS'], 'capital': 50000}
validated, error = validate_request(request8, RequestValidator.AnalyzeRequest)
if not error and validated:
    print_result(True, 'Single valid ticker accepted')
    print(f'  Validated tickers: {validated["tickers"]}')
    print(f'  Capital: {validated["capital"]}')
else:
    print_result(False, 'Single valid ticker should be accepted')
    if error:
        print(f'  Error: {error[0]["error"]["message"]}')
