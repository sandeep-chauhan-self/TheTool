"""
Test Strategy 1 vs Strategy 5 to see if they produce different results
"""

import sys
sys.path.insert(0, '.')

from utils.compute_score import analyze_ticker

def test_strategies():
    print('Testing TCS.NS with different strategies...')
    print()
    
    # Strategy 1 (Balanced)
    result1 = analyze_ticker('TCS.NS', strategy_id=1, capital=100000)
    print('=== Strategy 1 (Balanced) ===')
    print(f"Score: {result1.get('score', 'N/A')}")
    print(f"Verdict: {result1.get('verdict', 'N/A')}")
    print(f"Entry: {result1.get('entry', 'N/A')}")
    print(f"Target: {result1.get('target', 'N/A')}")
    print(f"Stop: {result1.get('stop', 'N/A')}")
    print(f"Strategy ID: {result1.get('strategy_id', 'N/A')}")
    print(f"Strategy Name: {result1.get('strategy_name', 'N/A')}")
    print()
    
    # Strategy 5 (4% Weekly)
    result5 = analyze_ticker('TCS.NS', strategy_id=5, capital=100000)
    print('=== Strategy 5 (4% Weekly) ===')
    print(f"Score: {result5.get('score', 'N/A')}")
    print(f"Verdict: {result5.get('verdict', 'N/A')}")
    print(f"Entry: {result5.get('entry', 'N/A')}")
    print(f"Target: {result5.get('target', 'N/A')}")
    print(f"Stop: {result5.get('stop', 'N/A')}")
    print(f"Strategy ID: {result5.get('strategy_id', 'N/A')}")
    print(f"Strategy Name: {result5.get('strategy_name', 'N/A')}")
    print()
    
    # Comparison
    score1 = result1.get('score', 0)
    score5 = result5.get('score', 0)
    
    print('=== COMPARISON ===')
    print(f"Score difference: {abs(score1 - score5):.4f}")
    print(f"Scores are different: {score1 != score5}")
    print(f"Verdicts are different: {result1.get('verdict') != result5.get('verdict')}")
    print(f"Targets are different: {result1.get('target') != result5.get('target')}")
    
    if score1 == score5:
        print()
        print("⚠️  WARNING: Scores are IDENTICAL - strategies not working differently!")
    else:
        print()
        print("✅ Scores are different - strategies working correctly!")

if __name__ == "__main__":
    test_strategies()
