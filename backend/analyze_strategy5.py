"""Analyze Strategy 5 backtest performance to find improvements."""

from utils.backtesting import BacktestEngine

def analyze_performance():
    """Deep analysis of Strategy 5 performance."""
    
    engine = BacktestEngine()
    result = engine.backtest_ticker('RELIANCE.NS', days=365)
    
    trades = result.get('trades', [])
    # Metrics are at top level, not nested
    metrics = {
        'win_rate': result.get('win_rate', 0),
        'total_pnl': result.get('total_profit_pct', 0),
        'avg_win': result.get('avg_win', 0),
        'avg_loss': result.get('avg_loss', 0),
        'profit_factor': result.get('profit_factor', 0),
        'expectancy': result.get('expectancy', 0),
    }
    
    print("=" * 70)
    print("STRATEGY 5 PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    print("\n=== CURRENT METRICS ===")
    print(f"Total Trades: {len(trades)}")
    print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
    print(f"Total P&L: {metrics.get('total_pnl', 0):.2f}%")
    print(f"Expectancy: {metrics.get('expectancy', 0):.2f}% per trade")
    print(f"Avg Win: {metrics.get('avg_win', 0):.2f}%")
    print(f"Avg Loss: {metrics.get('avg_loss', 0):.2f}%")
    print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    
    # Analyze exit reasons
    reasons = {}
    reason_pnl = {}
    for t in trades:
        r = t.get('reason', 'Unknown')
        pnl = t.get('pnl_pct', 0)
        reasons[r] = reasons.get(r, 0) + 1
        if r not in reason_pnl:
            reason_pnl[r] = []
        reason_pnl[r].append(pnl)
    
    print("\n=== EXIT REASONS BREAKDOWN ===")
    for r, count in sorted(reasons.items(), key=lambda x: -x[1]):
        pct = count / len(trades) * 100
        avg_pnl = sum(reason_pnl[r]) / len(reason_pnl[r])
        print(f"{r}: {count} trades ({pct:.1f}%), Avg P&L: {avg_pnl:+.2f}%")
    
    # Analyze by bars held
    print("\n=== WIN RATE BY BARS HELD ===")
    bars_stats = {}
    for t in trades:
        bars = t.get('bars_held', 0)
        outcome = t.get('outcome')
        pnl = t.get('pnl_pct', 0)
        if bars not in bars_stats:
            bars_stats[bars] = {'wins': 0, 'losses': 0, 'pnl': []}
        if outcome == 'WIN':
            bars_stats[bars]['wins'] += 1
        else:
            bars_stats[bars]['losses'] += 1
        bars_stats[bars]['pnl'].append(pnl)
    
    for bars in sorted(bars_stats.keys()):
        stats = bars_stats[bars]
        total = stats['wins'] + stats['losses']
        wr = stats['wins'] / total * 100 if total > 0 else 0
        avg_pnl = sum(stats['pnl']) / len(stats['pnl'])
        print(f"Bars {bars:2d}: {stats['wins']:3d}W / {stats['losses']:3d}L = {wr:5.1f}% WR, Avg P&L: {avg_pnl:+.2f}%")
    
    # Analyze by confidence level
    print("\n=== WIN RATE BY CONFIDENCE ===")
    conf_stats = {'high': {'wins': 0, 'losses': 0}, 'medium': {'wins': 0, 'losses': 0}, 'low': {'wins': 0, 'losses': 0}}
    for t in trades:
        conf = t.get('confidence', 0)
        outcome = t.get('outcome')
        if conf >= 0.7:
            bucket = 'high'
        elif conf >= 0.5:
            bucket = 'medium'
        else:
            bucket = 'low'
        if outcome == 'WIN':
            conf_stats[bucket]['wins'] += 1
        else:
            conf_stats[bucket]['losses'] += 1
    
    for bucket in ['high', 'medium', 'low']:
        stats = conf_stats[bucket]
        total = stats['wins'] + stats['losses']
        wr = stats['wins'] / total * 100 if total > 0 else 0
        print(f"Confidence {bucket:6s}: {stats['wins']:3d}W / {stats['losses']:3d}L = {wr:.1f}% win rate")
    
    # Stop loss analysis
    print("\n=== STOP LOSS ANALYSIS ===")
    stop_hits = [t for t in trades if 'stop' in t.get('reason', '').lower()]
    target_hits = [t for t in trades if 'target' in t.get('reason', '').lower()]
    time_exits = [t for t in trades if 'time' in t.get('reason', '').lower() or 'end of data' in t.get('reason', '').lower()]
    
    print(f"Stop Loss Hits: {len(stop_hits)} ({len(stop_hits)/len(trades)*100:.1f}%)")
    print(f"Target Hits: {len(target_hits)} ({len(target_hits)/len(trades)*100:.1f}%)")
    print(f"Time Exits: {len(time_exits)} ({len(time_exits)/len(trades)*100:.1f}%)")
    
    # Time exit analysis
    if time_exits:
        time_wins = [t for t in time_exits if t.get('outcome') == 'WIN']
        time_losses = [t for t in time_exits if t.get('outcome') == 'LOSS']
        time_avg_pnl = sum(t.get('pnl_pct', 0) for t in time_exits) / len(time_exits)
        print(f"\nTime Exit Details:")
        print(f"  - Wins: {len(time_wins)}, Losses: {len(time_losses)}")
        print(f"  - Win Rate: {len(time_wins)/len(time_exits)*100:.1f}%")
        print(f"  - Avg P&L: {time_avg_pnl:+.2f}%")
    
    # Suggestions
    print("\n" + "=" * 70)
    print("IMPROVEMENT SUGGESTIONS")
    print("=" * 70)
    
    win_rate = metrics.get('win_rate', 0)
    
    suggestions = []
    
    # Check stop loss frequency
    stop_pct = len(stop_hits) / len(trades) * 100 if trades else 0
    if stop_pct > 40:
        suggestions.append(f"1. HIGH STOP LOSS RATE ({stop_pct:.0f}%): Consider widening stop to 4% or using trailing stop")
    
    # Check target hit rate
    target_pct = len(target_hits) / len(trades) * 100 if trades else 0
    if target_pct < 20:
        suggestions.append(f"2. LOW TARGET HIT RATE ({target_pct:.0f}%): Consider lowering target from 5% to 4%")
    
    # Check time exit performance
    if time_exits:
        time_wr = len(time_wins) / len(time_exits) * 100
        if time_wr > 60:
            suggestions.append(f"3. TIME EXITS PROFITABLE ({time_wr:.0f}% WR): Consider extending holding period to 15 bars")
        elif time_wr < 40:
            suggestions.append(f"3. TIME EXITS LOSING ({time_wr:.0f}% WR): Consider reducing holding period to 7 bars")
    
    # Check win rate
    if win_rate < 50:
        suggestions.append("4. LOW WIN RATE: Add more signal filters (RSI range, volume confirmation)")
    
    if not suggestions:
        suggestions.append("Current strategy is performing well! Minor tweaks may help.")
    
    for s in suggestions:
        print(f"\n{s}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    analyze_performance()
