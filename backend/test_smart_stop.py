"""Test smart stop loss implementation."""

from utils.compute_score import analyze_ticker

def test_smart_stop():
    """Test Strategy 5 smart stop loss."""
    print("=" * 60)
    print("Testing Smart Stop Loss Implementation")
    print("=" * 60)
    
    # Test Strategy 5
    print("\n--- Strategy 5 (Aggressive with Smart Stop) ---")
    result5 = analyze_ticker(
        ticker='RELIANCE.NS',
        capital=100000,
        use_demo_data=True,
        strategy_id=5
    )
    
    print(f"Ticker: {result5.get('ticker')}")
    print(f"Score: {result5.get('score')}")
    print(f"Verdict: {result5.get('verdict')}")
    print(f"Entry: {result5.get('entry')}")
    print(f"Stop Loss: {result5.get('stop')}")  # Key is 'stop', not 'stop_loss'
    print(f"Target: {result5.get('target')}")
    
    entry5 = result5.get('entry', 0)
    stop5 = result5.get('stop', 0)  # Key is 'stop'
    target5 = result5.get('target', 0)
    
    if entry5 and stop5:
        # For Sell signals, stop is ABOVE entry
        # For Buy signals, stop is BELOW entry
        verdict5 = result5.get('verdict', '')
        if 'Sell' in verdict5:
            stop_pct = ((stop5 - entry5) / entry5) * 100
        else:
            stop_pct = ((entry5 - stop5) / entry5) * 100
        print(f"Calculated Stop %: {stop_pct:.2f}%")
    else:
        print(f"WARNING: Stop Loss is missing! Entry={entry5}, Stop={stop5}")
    
    if entry5 and target5:
        verdict5 = result5.get('verdict', '')
        if 'Sell' in verdict5:
            target_pct = ((entry5 - target5) / entry5) * 100
        else:
            target_pct = ((target5 - entry5) / entry5) * 100
        print(f"Calculated Target %: {target_pct:.2f}%")
    
    # Test Strategy 1 for comparison
    print("\n--- Strategy 1 (Balanced) ---")
    result1 = analyze_ticker(
        ticker='RELIANCE.NS',
        capital=100000,
        use_demo_data=True,
        strategy_id=1
    )
    
    print(f"Entry: {result1.get('entry')}")
    print(f"Stop Loss: {result1.get('stop')}")  # Key is 'stop'
    print(f"Target: {result1.get('target')}")
    
    entry1 = result1.get('entry', 0)
    stop1 = result1.get('stop', 0)
    
    if entry1 and stop1:
        verdict1 = result1.get('verdict', '')
        if 'Sell' in verdict1:
            stop_pct1 = ((stop1 - entry1) / entry1) * 100
        else:
            stop_pct1 = ((entry1 - stop1) / entry1) * 100
        print(f"Calculated Stop %: {stop_pct1:.2f}%")
    else:
        print(f"WARNING: Stop Loss is missing! Entry={entry1}, Stop={stop1}")
    
    print("\n" + "=" * 60)
    print("Expected Results:")
    print("- Strategy 5: Stop should be ~3-4% from entry (smart stop)")
    print("- Strategy 5: Target should be ~5% from entry")
    print("- Strategy 1: Stop should be ~2% from entry")
    print("=" * 60)

if __name__ == "__main__":
    test_smart_stop()
