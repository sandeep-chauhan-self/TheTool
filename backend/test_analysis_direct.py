#!/usr/bin/env python3
"""Quick test of analysis function"""

from utils.compute_score import analyze_ticker
import json

print("Testing analyze_ticker with TCS.NS (demo data)...")
result = analyze_ticker('TCS.NS', indicator_list=None, capital=100000, use_demo_data=True)

print(f"Verdict: {result.get('verdict')}")
print(f"Score: {result.get('score')}")
print(f"Entry: {result.get('entry')}")
print(f"Stop Loss: {result.get('stop_loss')}")
print(f"Target: {result.get('target')}")
print(f"Success: {result.get('success')}")
print(f"Data Valid: {result.get('data_valid')}")

if result.get('error'):
    print(f"Error: {result.get('error')}")

if result.get('data_message'):
    print(f"Data Message: {result.get('data_message')}")

print("\nFull result keys:", result.keys())
