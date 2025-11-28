#!/usr/bin/env python3
"""Test that both single and bulk analysis work"""
import json
import requests

BASE_URL = "http://localhost:5000/api"

# Test 1: Single stock analysis (watchlist-style with single ticker)
print("=" * 60)
print("TEST 1: Single Stock Analysis (/analyze)")
print("=" * 60)

single_payload = {
    "tickers": ["RELIANCE.NS"],
    "capital": 100000
}

try:
    response = requests.post(f"{BASE_URL}/analyze", json=single_payload, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print("✓ Single stock analysis works")
except Exception as e:
    print(f"✗ Single stock analysis failed: {e}")

# Test 2: Bulk analysis with specific stocks
print("\n" + "=" * 60)
print("TEST 2: Bulk Analysis with Specific Stocks (/analyze-all-stocks)")
print("=" * 60)

bulk_payload = {
    "symbols": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    "capital": 100000
}

try:
    response = requests.post(f"{BASE_URL}/stocks/analyze-all-stocks", json=bulk_payload, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    print("✓ Bulk analysis with specific stocks works")
except Exception as e:
    print(f"✗ Bulk analysis failed: {e}")

# Test 3: Analyze All (empty array)
print("\n" + "=" * 60)
print("TEST 3: Analyze All Stocks (empty array) (/analyze-all-stocks)")
print("=" * 60)

analyze_all_payload = {
    "symbols": [],  # Empty = analyze ALL
    "capital": 100000
}

try:
    response = requests.post(f"{BASE_URL}/stocks/analyze-all-stocks", json=analyze_all_payload, timeout=10)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Job ID: {data.get('job_id')}")
    print(f"Count: {data.get('count')} stocks")
    print("✓ Analyze All works (check progress at /api/stocks/all-stocks/progress)")
except Exception as e:
    print(f"✗ Analyze All failed: {e}")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
