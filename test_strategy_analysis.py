"""
Quick test script for strategy-based analysis
"""
import sys
sys.path.insert(0, './backend')

from utils.compute_score import analyze_ticker

# Test with different strategies
strategies_to_test = [1, 2, 3, 4]

print("=" * 60)
print("TESTING STRATEGY-BASED ANALYSIS")
print("=" * 60)

for strategy_id in strategies_to_test:
    result = analyze_ticker(
        'RELIANCE.NS', 
        capital=100000, 
        use_demo_data=True, 
        strategy_id=strategy_id
    )
    
    print(f"\nStrategy {strategy_id}: {result.get('strategy_name')}")
    print(f"  Score: {result.get('score')}")
    print(f"  Verdict: {result.get('verdict')}")
    print(f"  Entry: {result.get('entry')}")
    print(f"  Stop: {result.get('stop')}")
    print(f"  Target: {result.get('target')}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
