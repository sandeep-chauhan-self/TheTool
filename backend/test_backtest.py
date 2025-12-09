"""
Test backtesting engine
"""
import sys
sys.path.insert(0, '.')

from utils.backtesting import BacktestEngine

print('='*70)
print('BACKTESTING ENGINE TEST - Strategy 5')
print('='*70)
print()

# Create engine
engine = BacktestEngine(strategy_id=5)
print('✅ BacktestEngine initialized for Strategy 5')
print()

# Test single ticker
print('Testing: TCS.NS (30 days)')
print('-'*70)

try:
    result = engine.backtest_ticker('TCS.NS', days=30)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print('✅ Backtest Complete!')
        print(f"   Ticker: {result['ticker']}")
        print(f"   Period: {result['backtest_period']}")
        print(f"   Total Signals: {result['total_signals']}")
        print(f"   Win Rate: {result['win_rate']}%")
        print(f"   Profit Factor: {result['profit_factor']}x")
        print(f"   Total P&L: {result['total_profit_pct']}%")
        print(f"   Avg Win: {result['avg_win']}%")
        print(f"   Avg Loss: {result['avg_loss']}%")
        print(f"   Max Drawdown: {result['max_drawdown']}%")
        print(f"   Consecutive Wins: {result['consecutive_wins']}")
        
        if result.get('trades'):
            print()
            print('   First 3 Trades:')
            for i, trade in enumerate(result['trades'][:3]):
                outcome = trade['outcome']
                pnl = trade['pnl_pct']
                reason = trade['reason']
                entry = trade['entry_price']
                print(f'     Trade {i+1}: Entry ₹{entry:.2f} → {outcome} ({pnl:+.2f}%) - {reason}')
        
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()

print()
print('='*70)
