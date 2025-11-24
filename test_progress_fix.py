"""
Test script to verify progress polling and result display fix
"""
import json
import requests
import time
import sys

API_BASE = "http://localhost:5000"

def test_progress_endpoint():
    """Test the progress endpoint"""
    print("\n[TEST 1] Progress Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/stocks/all-stocks/progress", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response structure valid")
            print(f"  - is_analyzing: {data.get('is_analyzing')}")
            print(f"  - analyzing: {data.get('analyzing')}")
            print(f"  - total: {data.get('total')}")
            print(f"  - completed: {data.get('completed')}")
            print(f"  - percentage: {data.get('percentage')}%")
            print(f"  - Active jobs: {len([j for j in data.get('jobs', []) if j['status'] in ('queued', 'processing')])}")
            print(f"  - Completed jobs shown: {len([j for j in data.get('jobs', []) if j['status'] in ('completed', 'cancelled', 'failed')])}")
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_analysis_job_creation():
    """Test creating an analysis job"""
    print("\n[TEST 2] Analysis Job Creation")
    print("=" * 60)
    
    try:
        # First, add a stock to watchlist
        add_response = requests.post(f"{API_BASE}/api/watchlist", json={
            "symbols": ["INFY"]
        }, timeout=10)
        print(f"Added INFY to watchlist: {add_response.status_code}")
        
        # Start analysis
        response = requests.post(f"{API_BASE}/api/stocks/analyze-all-stocks", json={
            "symbols": ["INFY"],
            "capital": 100000,
            "force": False
        }, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in (200, 201):
            data = response.json()
            print(f"✓ Job created successfully")
            print(f"  - Job ID: {data.get('job_id')}")
            print(f"  - Status: {data.get('status')}")
            print(f"  - Total: {data.get('total')}")
            print(f"  - Is duplicate: {data.get('is_duplicate')}")
            return True, data.get('job_id')
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, None


def test_result_visibility(job_id=None):
    """Test that results are visible after analysis"""
    print("\n[TEST 3] Result Visibility")
    print("=" * 60)
    
    try:
        # Get results
        response = requests.get(f"{API_BASE}/api/stocks/all-stocks/results?page=1&per_page=10", timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Results endpoint working")
            print(f"  - Total results: {data.get('total')}")
            print(f"  - Results on page 1: {data.get('count')}")
            
            if data.get('count', 0) > 0:
                result = data['results'][0]
                print(f"  - Sample result: {result.get('symbol')} - Score: {result.get('score')}")
            
            return True
        else:
            print(f"✗ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("PROGRESS POLLING FIX VERIFICATION")
    print("=" * 60)
    
    # Test 1: Progress endpoint
    test1_passed = test_progress_endpoint()
    
    # Test 2: Job creation
    test2_passed, job_id = test_analysis_job_creation()
    
    # Test 3: Results
    test3_passed = test_result_visibility(job_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Progress Endpoint: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"Job Creation: {'✓ PASS' if test2_passed else '✗ FAIL'}")
    print(f"Result Visibility: {'✓ PASS' if test3_passed else '✗ FAIL'}")
    print()
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
