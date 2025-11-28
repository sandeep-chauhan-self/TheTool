#!/usr/bin/env python3
"""Test a single stock analysis to see what's failing"""
import sys
sys.path.insert(0, '.')

from utils.compute_score import analyze_ticker

# Test with a single stock
ticker = "20MICRONS.NS"
result = analyze_ticker(ticker, indicator_list=None, capital=100000, use_demo_data=False)

print(f"Analysis for {ticker}:")
print(f"  Success: {result.get('success', False)}")
print(f"  Verdict: {result.get('verdict')}")
print(f"  Score: {result.get('score')}")
print(f"  Error: {result.get('error')}")
print(f"  Data Valid: {result.get('data_valid')}")
print(f"  Data Message: {result.get('data_message')}")

if not result.get('success'):
    print(f"\n FAILURE DETAILS:")
    print(f"  Full Result: {result}")
