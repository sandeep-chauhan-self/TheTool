"""
Test script to validate the duplicate job detection and fix
Tests:
1. First request creates a job and starts analysis
2. Duplicate request returns 200 with is_duplicate=true
3. Force=true bypasses duplicate check
"""

import requests
import json
import time
import sys

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "_ZQmwHptTFGeAyWWaWXGs1KlJwrZNZFVbxpurC3evBI"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_analyze_all_stocks():
    """Test analyze-all-stocks endpoint with duplicate detection"""
    
    print("\n" + "="*80)
    print("TEST 1: First request - should create job and return 201")
    print("="*80)
    
    payload = {"symbols": ["20MICRONS.NS"]}
    
    response = requests.post(
        f"{API_BASE}/api/stocks/analyze-all-stocks",
        json=payload,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 201:
        print("❌ FAILED: Expected 201, got", response.status_code)
        return None
    
    data = response.json()
    job_id_1 = data.get("job_id")
    
    if not job_id_1:
        print("❌ FAILED: No job_id in response")
        return None
    
    print(f"✅ PASSED: Job created with ID {job_id_1}")
    print(f"   Thread started: {data.get('thread_started', False)}")
    
    # Wait a bit for thread to start
    time.sleep(2)
    
    print("\n" + "="*80)
    print("TEST 2: Duplicate request - should return 200 with is_duplicate=true")
    print("="*80)
    
    response = requests.post(
        f"{API_BASE}/api/stocks/analyze-all-stocks",
        json=payload,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code != 200:
        print(f"⚠️  WARNING: Expected 200, got {response.status_code}")
        print("   (409 is acceptable if duplicate check triggers)")
        if response.status_code == 409:
            print("   This means duplicate was detected - job_id collision")
            return job_id_1
    
    data = response.json()
    job_id_2 = data.get("job_id")
    is_duplicate = data.get("is_duplicate", False)
    
    if job_id_2 == job_id_1 and is_duplicate:
        print(f"✅ PASSED: Duplicate detected correctly")
        print(f"   Returned existing job_id: {job_id_2}")
        print(f"   Status: {data.get('status')}")
        print(f"   Progress: {data.get('completed')}/{data.get('total')}")
    else:
        print(f"⚠️  Different behavior:")
        print(f"   Job ID 1: {job_id_1}")
        print(f"   Job ID 2: {job_id_2}")
        print(f"   Is duplicate: {is_duplicate}")
    
    print("\n" + "="*80)
    print("TEST 3: Force=true - should create new job even with duplicates")
    print("="*80)
    
    payload_force = {"symbols": ["20MICRONS.NS"], "force": True}
    
    response = requests.post(
        f"{API_BASE}/api/stocks/analyze-all-stocks",
        json=payload_force,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        data = response.json()
        job_id_3 = data.get("job_id")
        if job_id_3 != job_id_1:
            print(f"✅ PASSED: New job created with force=true")
            print(f"   Job ID 1: {job_id_1}")
            print(f"   Job ID 3: {job_id_3}")
        else:
            print(f"⚠️  WARNING: Same job_id returned despite force=true")
    else:
        print(f"⚠️  WARNING: Expected 201 with force=true, got {response.status_code}")
    
    print("\n" + "="*80)
    print("TEST 4: Check job status")
    print("="*80)
    
    response = requests.get(
        f"{API_BASE}/api/analysis/status/{job_id_1}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Job status retrieved:")
        print(f"   Status: {data.get('status')}")
        print(f"   Progress: {data.get('completed')}/{data.get('total')}")
    else:
        print(f"⚠️  Failed to get job status: {response.status_code}")


def test_analyze_endpoint():
    """Test /analyze endpoint with duplicate detection"""
    
    print("\n" + "="*80)
    print("TEST 5: Analyze endpoint - first request")
    print("="*80)
    
    payload = {"tickers": ["TCS.NS"], "capital": 100000}
    
    response = requests.post(
        f"{API_BASE}/api/analysis/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code not in [200, 201]:
        print(f"⚠️  Unexpected status: {response.status_code}")
        return
    
    data = response.json()
    job_id = data.get("job_id")
    print(f"✅ Job created: {job_id}")
    
    time.sleep(1)
    
    print("\n" + "="*80)
    print("TEST 6: Analyze endpoint - duplicate request")
    print("="*80)
    
    response = requests.post(
        f"{API_BASE}/api/analysis/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200 and response.json().get("is_duplicate"):
        print(f"✅ PASSED: Duplicate detected and returned with 200")
    else:
        print(f"⚠️  Different behavior: status={response.status_code}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DUPLICATE JOB DETECTION TEST SUITE")
    print("="*80)
    print(f"Target: {API_BASE}")
    print(f"Testing analyze-all-stocks and analyze endpoints")
    
    try:
        test_analyze_all_stocks()
        test_analyze_endpoint()
        
        print("\n" + "="*80)
        print("TEST SUITE COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
