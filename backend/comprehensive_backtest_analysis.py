"""
Comprehensive Backtest Analysis for Strategy 5

Analyzes 15 NSE stocks to identify:
1. Overall performance metrics
2. Exit reason breakdown (target/stop/time)
3. Bars held analysis
4. Confidence correlation with win rate
5. Per-stock performance
6. Improvement opportunities
"""

from utils.backtesting import BacktestEngine

def run_analysis():
    # Test on multiple NSE stocks
    test_stocks = [
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'SBIN.NS', 'WIPRO.NS', 'LT.NS', 'AXISBANK.NS',
        'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'BAJFINANCE.NS', 'ASIANPAINT.NS'
    ]

    engine = BacktestEngine(strategy_id=5)
    print('Strategy 5 Comprehensive Backtest Analysis')
    print('=' * 70)
    print(f'ADX Filter: {engine.USE_ADX_FILTER} (threshold: {engine.ADX_CHOPPY_THRESHOLD})')
    print(f'Strategy 5 Validation: {engine.USE_STRATEGY5_VALIDATION}')
    print(f'Target: {engine.TARGET_PCT}%, Stop: {engine.STOP_LOSS_PCT}%, Max Bars: {engine.MAX_BARS}')
    print('=' * 70)

    all_trades = []
    results_summary = []

    for ticker in test_stocks:
        result = engine.backtest_ticker(ticker, days=90)
        if 'error' not in result and result.get('total_signals', 0) > 0:
            results_summary.append({
                'ticker': ticker,
                'signals': result.get('total_signals', 0),
                'win_rate': result.get('win_rate', 0),
                'expectancy': result.get('expectancy', 0),
                'profit_factor': result.get('profit_factor', 0),
                'total_pnl': result.get('total_profit_pct', 0)
            })
            if result.get('trades'):
                all_trades.extend(result['trades'])

    print(f'\nAnalyzed {len(results_summary)} stocks with valid signals')
    print()

    # Aggregate metrics
    total_signals = sum(r['signals'] for r in results_summary)
    total_wins = sum(1 for t in all_trades if t['outcome'] == 'WIN')
    total_losses = sum(1 for t in all_trades if t['outcome'] == 'LOSS')

    print('AGGREGATE METRICS:')
    print(f'  Total Signals: {total_signals}')
    print(f'  Winning Trades: {total_wins}')
    print(f'  Losing Trades: {total_losses}')
    if total_signals > 0:
        print(f'  Overall Win Rate: {total_wins/total_signals*100:.1f}%')
        
        # Overall expectancy
        total_pnl = sum(t['pnl_pct'] for t in all_trades)
        print(f'  Overall Expectancy: {total_pnl/total_signals:.2f}% per trade')
        print(f'  Total P&L: {total_pnl:.2f}%')

    # Calculate exit reason breakdown
    target_hits = sum(1 for t in all_trades if 'target' in t.get('reason', '').lower())
    stop_hits = sum(1 for t in all_trades if 'stop' in t.get('reason', '').lower())
    time_exits = sum(1 for t in all_trades if 'time' in t.get('reason', '').lower() or 'end' in t.get('reason', '').lower())

    print()
    print('EXIT REASON BREAKDOWN:')
    if total_signals > 0:
        print(f'  Target Hit ({engine.TARGET_PCT}%): {target_hits} ({target_hits/total_signals*100:.1f}%)')
        print(f'  Stop Loss Hit: {stop_hits} ({stop_hits/total_signals*100:.1f}%)')
        print(f'  Time Exit ({engine.MAX_BARS} bars): {time_exits} ({time_exits/total_signals*100:.1f}%)')

    # Time exit analysis
    if time_exits > 0:
        time_exit_wins = sum(1 for t in all_trades if ('time' in t.get('reason', '').lower() or 'end' in t.get('reason', '').lower()) and t['outcome'] == 'WIN')
        print(f'  Time Exit Win Rate: {time_exit_wins/time_exits*100:.1f}%')

    # Average P&L by exit type
    target_pnl = [t['pnl_pct'] for t in all_trades if 'target' in t.get('reason', '').lower()]
    stop_pnl = [t['pnl_pct'] for t in all_trades if 'stop' in t.get('reason', '').lower()]
    time_pnl = [t['pnl_pct'] for t in all_trades if 'time' in t.get('reason', '').lower() or 'end' in t.get('reason', '').lower()]

    print()
    print('AVERAGE P&L BY EXIT TYPE:')
    if target_pnl:
        print(f'  Target Hit: +{sum(target_pnl)/len(target_pnl):.2f}%')
    if stop_pnl:
        print(f'  Stop Loss: {sum(stop_pnl)/len(stop_pnl):.2f}%')
    if time_pnl:
        print(f'  Time Exit: {sum(time_pnl)/len(time_pnl):+.2f}%')

    # Bars held analysis
    bars_held = [t.get('bars_held', 0) for t in all_trades]
    win_bars = [t.get('bars_held', 0) for t in all_trades if t['outcome'] == 'WIN']
    loss_bars = [t.get('bars_held', 0) for t in all_trades if t['outcome'] == 'LOSS']

    print()
    print('BARS HELD ANALYSIS:')
    if bars_held:
        print(f'  Average Bars Held: {sum(bars_held)/len(bars_held):.1f}')
    if win_bars:
        print(f'  Winning Trades Avg Bars: {sum(win_bars)/len(win_bars):.1f}')
    if loss_bars:
        print(f'  Losing Trades Avg Bars: {sum(loss_bars)/len(loss_bars):.1f}')

    # Distribution of bars held for wins
    print()
    print('BARS HELD DISTRIBUTION (Winning Trades):')
    for bars in range(1, engine.MAX_BARS + 1):
        count = sum(1 for t in all_trades if t['outcome'] == 'WIN' and t.get('bars_held', 0) == bars)
        if count > 0:
            print(f'  {bars:2d} bars: {count:3d} wins')

    # Confidence analysis
    high_conf_trades = [t for t in all_trades if t.get('confidence', 0) >= 100]
    med_conf_trades = [t for t in all_trades if 80 <= t.get('confidence', 0) < 100]
    low_conf_trades = [t for t in all_trades if t.get('confidence', 0) < 80]

    print()
    print('CONFIDENCE ANALYSIS:')
    if high_conf_trades:
        high_wins = sum(1 for t in high_conf_trades if t['outcome'] == 'WIN')
        high_pnl = sum(t['pnl_pct'] for t in high_conf_trades)
        print(f'  High Confidence (100): {len(high_conf_trades)} trades, {high_wins/len(high_conf_trades)*100:.1f}% win rate, {high_pnl/len(high_conf_trades):.2f}% avg')
    if med_conf_trades:
        med_wins = sum(1 for t in med_conf_trades if t['outcome'] == 'WIN')
        med_pnl = sum(t['pnl_pct'] for t in med_conf_trades)
        print(f'  Med Confidence (80-99): {len(med_conf_trades)} trades, {med_wins/len(med_conf_trades)*100:.1f}% win rate, {med_pnl/len(med_conf_trades):.2f}% avg')
    if low_conf_trades:
        low_wins = sum(1 for t in low_conf_trades if t['outcome'] == 'WIN')
        low_pnl = sum(t['pnl_pct'] for t in low_conf_trades)
        print(f'  Low Confidence (<80): {len(low_conf_trades)} trades, {low_wins/len(low_conf_trades)*100:.1f}% win rate, {low_pnl/len(low_conf_trades):.2f}% avg')

    # RSI analysis
    print()
    print('RSI AT ENTRY ANALYSIS:')
    rsi_ranges = [(30, 40), (40, 50), (50, 60), (60, 70), (70, 75)]
    for low, high in rsi_ranges:
        range_trades = [t for t in all_trades if low <= t.get('rsi', 50) < high]
        if range_trades:
            range_wins = sum(1 for t in range_trades if t['outcome'] == 'WIN')
            range_pnl = sum(t['pnl_pct'] for t in range_trades)
            print(f'  RSI {low}-{high}: {len(range_trades)} trades, {range_wins/len(range_trades)*100:.1f}% win, {range_pnl/len(range_trades):.2f}% avg')

    # ADX analysis
    print()
    print('ADX AT ENTRY ANALYSIS:')
    adx_ranges = [(20, 25), (25, 30), (30, 40), (40, 50), (50, 100)]
    for low, high in adx_ranges:
        range_trades = [t for t in all_trades if low <= t.get('adx', 25) < high]
        if range_trades:
            range_wins = sum(1 for t in range_trades if t['outcome'] == 'WIN')
            range_pnl = sum(t['pnl_pct'] for t in range_trades)
            print(f'  ADX {low}-{high}: {len(range_trades)} trades, {range_wins/len(range_trades)*100:.1f}% win, {range_pnl/len(range_trades):.2f}% avg')

    # Volume ratio analysis
    print()
    print('VOLUME RATIO AT ENTRY ANALYSIS:')
    vol_ranges = [(0, 1.0), (1.0, 1.3), (1.3, 1.5), (1.5, 2.0), (2.0, 100)]
    for low, high in vol_ranges:
        range_trades = [t for t in all_trades if low <= t.get('volume_ratio', 1.0) < high]
        if range_trades:
            range_wins = sum(1 for t in range_trades if t['outcome'] == 'WIN')
            range_pnl = sum(t['pnl_pct'] for t in range_trades)
            label = f'{low:.1f}-{high:.1f}' if high < 100 else f'{low:.1f}+'
            print(f'  Volume {label}x: {len(range_trades)} trades, {range_wins/len(range_trades)*100:.1f}% win, {range_pnl/len(range_trades):.2f}% avg')

    # Per-stock breakdown
    print()
    print('PER-STOCK RESULTS:')
    print('-' * 70)
    print(f"{'Ticker':15s} | {'Signals':>7s} | {'Win%':>6s} | {'Expect':>7s} | {'PF':>5s} | {'Total':>7s}")
    print('-' * 70)
    for r in sorted(results_summary, key=lambda x: x['expectancy'], reverse=True):
        print(f"{r['ticker']:15s} | {r['signals']:7d} | {r['win_rate']:5.1f}% | {r['expectancy']:+6.2f}% | {r['profit_factor']:5.2f} | {r['total_pnl']:+6.1f}%")

    # Improvement recommendations
    print()
    print('=' * 70)
    print('IMPROVEMENT RECOMMENDATIONS:')
    print('=' * 70)
    
    # Check if high ADX performs better
    high_adx_trades = [t for t in all_trades if t.get('adx', 25) >= 30]
    low_adx_trades = [t for t in all_trades if 20 <= t.get('adx', 25) < 30]
    
    if high_adx_trades and low_adx_trades:
        high_adx_win = sum(1 for t in high_adx_trades if t['outcome'] == 'WIN') / len(high_adx_trades) * 100
        low_adx_win = sum(1 for t in low_adx_trades if t['outcome'] == 'WIN') / len(low_adx_trades) * 100
        
        if high_adx_win > low_adx_win + 5:
            print(f'\n1. RAISE ADX THRESHOLD: ADX>=30 has {high_adx_win:.1f}% win rate vs {low_adx_win:.1f}% for ADX 20-30')
            print('   Consider raising ADX_CHOPPY_THRESHOLD from 20 to 25 or 30')
    
    # Check volume correlation
    high_vol_trades = [t for t in all_trades if t.get('volume_ratio', 1.0) >= 1.5]
    low_vol_trades = [t for t in all_trades if t.get('volume_ratio', 1.0) < 1.5]
    
    if high_vol_trades and low_vol_trades:
        high_vol_win = sum(1 for t in high_vol_trades if t['outcome'] == 'WIN') / len(high_vol_trades) * 100
        low_vol_win = sum(1 for t in low_vol_trades if t['outcome'] == 'WIN') / len(low_vol_trades) * 100
        
        if high_vol_win > low_vol_win + 5:
            print(f'\n2. RE-ENABLE VOLUME FILTER: Volume>=1.5x has {high_vol_win:.1f}% win rate vs {low_vol_win:.1f}% for lower volume')
            print('   Consider setting REQUIRE_VOLUME_FILTER = True with MIN_VOLUME_RATIO = 1.5')
    
    # Check time exit optimization
    if time_exits > 0 and time_pnl:
        time_win_rate = sum(1 for t in all_trades if ('time' in t.get('reason', '').lower() or 'end' in t.get('reason', '').lower()) and t['outcome'] == 'WIN') / time_exits * 100
        time_avg_pnl = sum(time_pnl) / len(time_pnl)
        
        if time_win_rate < 60:
            print(f'\n3. REDUCE MAX_BARS: Time exits have only {time_win_rate:.1f}% win rate')
            print('   Consider reducing MAX_BARS from 15 to 10 or 12')
        elif time_avg_pnl > 1.0:
            print(f'\n3. INCREASE MAX_BARS: Time exits average +{time_avg_pnl:.2f}% profit')
            print('   Consider increasing MAX_BARS from 15 to 18 or 20')
    
    # Check target optimization
    if target_hits > 0:
        target_hit_rate = target_hits / total_signals * 100
        if target_hit_rate < 30:
            print(f'\n4. LOWER TARGET: Only {target_hit_rate:.1f}% of trades hit the {engine.TARGET_PCT}% target')
            print('   Consider reducing TARGET_PCT from 4% to 3% or 3.5%')
        elif target_hit_rate > 50:
            print(f'\n4. RAISE TARGET: {target_hit_rate:.1f}% of trades hit the {engine.TARGET_PCT}% target')
            print('   Consider increasing TARGET_PCT from 4% to 4.5% or 5%')
    
    # Check RSI sweet spot
    best_rsi_range = None
    best_rsi_win = 0
    for low, high in rsi_ranges:
        range_trades = [t for t in all_trades if low <= t.get('rsi', 50) < high]
        if len(range_trades) >= 5:
            range_win = sum(1 for t in range_trades if t['outcome'] == 'WIN') / len(range_trades) * 100
            if range_win > best_rsi_win:
                best_rsi_win = range_win
                best_rsi_range = (low, high)
    
    if best_rsi_range and best_rsi_win > 70:
        print(f'\n5. RSI SWEET SPOT: RSI {best_rsi_range[0]}-{best_rsi_range[1]} has {best_rsi_win:.1f}% win rate')
        print(f'   Consider tightening RSI_MIN={best_rsi_range[0]} and RSI_MAX={best_rsi_range[1]}')


if __name__ == '__main__':
    run_analysis()
