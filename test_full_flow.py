#!/usr/bin/env python3
"""
Test the complete analysis workflow:
1. Start bulk analysis
2. Check progress
3. Wait for completion
4. Verify results are stored
"""
import json
import time
import requests
import requests.exceptions
import os
from datetime import datetime

# Get API base URL from config or environment, default to development port 5000
try:
    from backend.constants import get_api_base_url
    API_BASE = get_api_base_url()
except (ImportError, Exception):
    # Fallback: use environment variable or default to localhost:5000
    API_BASE = os.getenv('API_BASE_URL', 'http://localhost:5000')

WAIT_TIMEOUT = 300  # 5 minutes
POLL_INTERVAL = 5   # 5 seconds
REQUEST_TIMEOUT = 10  # 10 seconds for individual requests

def test_analysis_flow():
    """Test complete analysis workflow"""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE ANALYSIS WORKFLOW")
    print("=" * 60)
    
    # Step 1: Start analysis
    print("\n[STEP 1] Starting bulk analysis for 1 stock...")
    try:
        response = requests.post(
            f"{API_BASE}/api/stocks/analyze-all-stocks",
            json={"symbols": ["RELIANCE.NS"]},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        try:
            job_data = response.json()
            job_id = job_data.get("job_id")
            print(f"✓ Analysis job created: {job_id}")
            print(f"  - Status: {job_data.get('status')}")
            print(f"  - Count: {job_data.get('count')}")
        except (ValueError, KeyError) as parse_error:
            print(f"✗ Error parsing response JSON: {parse_error}")
            return False
    except requests.exceptions.RequestException as req_error:
        print(f"✗ Error starting analysis (HTTP/Network): {req_error}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error starting analysis: {e}")
        return False
    
    # Step 2: Poll progress
    print("\n[STEP 2] Polling progress...")
    start_time = time.time()
    completed = False
    
    while (time.time() - start_time) < WAIT_TIMEOUT:
        try:
            response = requests.get(f"{API_BASE}/api/stocks/all-stocks/progress", timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            try:
                progress = response.json()
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress Update:")
                print(f"  - Is analyzing: {progress.get('is_analyzing')}")
                print(f"  - Completed: {progress.get('completed')}/{progress.get('total')}")
                print(f"  - Percentage: {progress.get('percentage')}%")
                print(f"  - Successful: {progress.get('successful')}")
                print(f"  - Failed: {progress.get('failed')}")
                
                if not progress.get('is_analyzing') and progress.get('analyzing') == 0:
                    print("✓ Analysis completed!")
                    completed = True
                    break
                
                time.sleep(POLL_INTERVAL)
            except (ValueError, KeyError) as parse_error:
                print(f"✗ Error parsing progress JSON: {parse_error}")
                return False
        except requests.exceptions.RequestException as req_error:
            print(f"✗ Error polling progress (HTTP/Network): {req_error}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error polling progress: {e}")
            return False
    
    if not completed:
        print("✗ Analysis timed out")
        return False
    
    # Step 3: Check results
    print("\n[STEP 3] Fetching analysis results...")
    try:
        response = requests.get(f"{API_BASE}/api/stocks/all-stocks/results")
        if response.status_code != 200:
            print(f"✗ Failed to get results: {response.status_code}")
            return False
        
        results = response.json()
        print(f"✓ Retrieved results:")
        print(f"  - Total: {results.get('total')}")
        print(f"  - Count: {results.get('count')}")
        
        if results.get('results'):
            for result in results.get('results', [])[:5]:  # Show first 5
                print(f"\n  Result: {result.get('symbol')}")
                print(f"    - Verdict: {result.get('verdict')}")
                print(f"    - Score: {result.get('score')}")
                print(f"    - Entry: {result.get('entry')}")
                print(f"    - Target: {result.get('target')}")
    except Exception as e:
        print(f"✗ Error fetching results: {e}")
        return False
    
    # Step 4: Check history for specific stock
    print("\n[STEP 4] Fetching history for RELIANCE...")
    try:
        response = requests.get(f"{API_BASE}/api/stocks/all-stocks/RELIANCE/history")
        if response.status_code != 200:
            print(f"✗ Failed to get history: {response.status_code}")
            return False
        
        history = response.json()
        print(f"✓ Retrieved history:")
        print(f"  - Symbol: {history.get('symbol')}")
        print(f"  - Count: {history.get('count')}")
        
        if history.get('history'):
            h = history['history'][0]
            print(f"\n  Latest: {h.get('symbol')}")
            print(f"    - Verdict: {h.get('verdict')}")
            print(f"    - Score: {h.get('score')}")
    except Exception as e:
        print(f"✗ Error fetching history: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ WORKFLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_analysis_flow()
    exit(0 if success else 1)
