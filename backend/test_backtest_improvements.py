"""
Quick test of improved backtesting engine
"""

import sys
sys.path.insert(0, '.')

from utils.backtesting import BacktestEngine

def test_backtest():
    print("Testing improved BacktestEngine...")
    print("=" * 50)
    
    bt = BacktestEngine()
    result = bt.backtest_ticker('TCS.NS', days=90)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    print(f"\nBacktest Results for {result.get('ticker', 'N/A')}")
    print(f"Period: {result.get('backtest_period', 'N/A')}")
    print("-" * 50)
    
    print(f"Total Signals: {result.get('total_signals', 0)}")
    print(f"Winning Trades: {result.get('winning_trades', 0)}")
    print(f"Losing Trades: {result.get('losing_trades', 0)}")
    print(f"Win Rate: {result.get('win_rate', 0)}%")
    print(f"Profit Factor: {result.get('profit_factor', 0)}")
    print(f"Total Profit: {result.get('total_profit_pct', 0)}%")
    print(f"Expectancy: {result.get('expectancy', 0)}%")
    print(f"Avg Win: {result.get('avg_win', 0)}%")
    print(f"Avg Loss: {result.get('avg_loss', 0)}%")
    print(f"Max Drawdown: {result.get('max_drawdown', 0)}%")
    print(f"Consecutive Wins: {result.get('consecutive_wins', 0)}")
    
    # Show a few trades
    trades = result.get('trades', [])
    if trades:
        print(f"\nSample Trades (showing first 5):")
        for i, trade in enumerate(trades[:5]):
            print(f"  {i+1}. {trade.get('entry_date', 'N/A')} - {trade.get('outcome', 'N/A')}: "
                  f"Entry={trade.get('entry_price', 0)}, Exit={trade.get('exit_price', 0)}, "
                  f"P&L={trade.get('pnl_pct', 0)}%, RSI={trade.get('rsi', 'N/A')}, "
                  f"Reason={trade.get('reason', 'N/A')}")

if __name__ == "__main__":
    test_backtest()
