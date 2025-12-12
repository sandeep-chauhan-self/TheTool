"""Test backtest reason field matches bars_held."""

from utils.backtesting import BacktestEngine

def test_backtest_reasons():
    """Check if bars_held and reason are consistent."""
    engine = BacktestEngine()
    result = engine.backtest_ticker('RELIANCE.NS', days=365)
    
    print("=" * 70)
    print("Backtest Trade Results - Checking bars_held vs reason consistency")
    print("=" * 70)
    
    trades = result.get('trades', [])
    print(f"\nTotal trades: {len(trades)}\n")
    
    issues = []
    
    for i, trade in enumerate(trades):
        bars = trade.get('bars_held')
        reason = trade.get('reason', '')
        outcome = trade.get('outcome')
        pnl = trade.get('pnl_pct', 0)
        
        # Check for inconsistency
        has_issue = False
        if bars < 10 and 'Time exit (10 bars)' in reason:
            has_issue = True
            issues.append(f"Trade {i+1}: bars={bars} but reason says '10 bars'")
        
        status = "❌ BUG!" if has_issue else "✓"
        print(f"Trade {i+1}: bars={bars:2d}, outcome={outcome:4s}, pnl={pnl:+6.2f}%, reason=\"{reason}\" {status}")
    
    print("\n" + "=" * 70)
    if issues:
        print(f"FOUND {len(issues)} ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ All trades have consistent bars_held and reason!")
    print("=" * 70)

if __name__ == "__main__":
    test_backtest_reasons()
