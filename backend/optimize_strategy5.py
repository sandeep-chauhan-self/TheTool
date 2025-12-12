"""
Optimize Strategy 5 parameters for maximum winning results.
Tests different combinations of:
- Target percentage (3%, 4%, 5%)
- Stop loss percentage (3%, 4%, 5%)
- Holding period (10, 15, 20 bars)
- Signal filters (RSI bounds, volume confirmation)
"""

import sys
import json
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

# Test tickers - diversified NSE stocks
TEST_TICKERS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'SUNPHARMA.NS', 'TATAMOTORS.NS', 'WIPRO.NS'
]


def calculate_indicators(df):
    """Calculate technical indicators for signal generation."""
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    
    # Volume SMA
    df['Vol_SMA'] = df['Volume'].rolling(window=20).mean()
    
    # ATR for smart stop
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # EMA 20
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    return df


def generate_signal(row, prev_row, rsi_lower=30, rsi_upper=70, require_volume=True):
    """Generate buy signal based on indicators with configurable filters."""
    try:
        # Extract scalar values (handling both Series and scalar cases)
        def get_val(series_or_scalar):
            if hasattr(series_or_scalar, 'iloc'):
                return float(series_or_scalar.iloc[0])
            return float(series_or_scalar)
        
        rsi = get_val(row['RSI'])
        macd = get_val(row['MACD'])
        macd_signal = get_val(row['MACD_Signal'])
        prev_rsi = get_val(prev_row['RSI'])
        prev_macd = get_val(prev_row['MACD'])
        prev_macd_signal = get_val(prev_row['MACD_Signal'])
        close = get_val(row['Close'])
        bb_mid = get_val(row['BB_Mid'])
        bb_lower = get_val(row['BB_Lower'])
        ema20 = get_val(row['EMA20'])
        volume = get_val(row['Volume'])
        vol_sma = get_val(row['Vol_SMA'])
        
        if np.isnan(rsi) or np.isnan(macd):
            return 0
    except (TypeError, ValueError, KeyError, IndexError):
        return 0
    
    signals = 0
    
    # RSI oversold bounce
    if rsi < rsi_upper and rsi > rsi_lower:
        if not np.isnan(prev_rsi) and prev_rsi < rsi_lower:  # Bouncing from oversold
            signals += 1
    
    # MACD bullish crossover
    if not np.isnan(prev_macd) and not np.isnan(prev_macd_signal):
        if macd > macd_signal and prev_macd <= prev_macd_signal:
            signals += 1
    
    # Price near lower Bollinger Band (mean reversion)
    if not np.isnan(bb_mid) and not np.isnan(bb_lower):
        if close < bb_mid and close > bb_lower:
            signals += 1
    
    # Price above EMA20 (trend following)
    if not np.isnan(ema20):
        if close > ema20:
            signals += 1
    
    # Volume confirmation
    if require_volume and not np.isnan(vol_sma):
        if volume < vol_sma * 0.8:  # Low volume = weak signal
            signals -= 1
        elif volume > vol_sma * 1.2:  # High volume = strong signal
            signals += 1
    
    # Need at least 2 signals for a buy
    return 1 if signals >= 2 else 0


def calculate_stop_loss(entry_price, atr, base_pct=3, atr_mult=1.5, max_pct=4):
    """Calculate smart stop loss using ATR."""
    # Base stop
    base_stop = entry_price * (1 - base_pct / 100)
    
    # ATR-based stop
    try:
        atr_val = float(atr.iloc[0]) if hasattr(atr, 'iloc') else float(atr)
        if not np.isnan(atr_val) and atr_val > 0:
            atr_stop = entry_price - (atr_val * atr_mult)
        else:
            atr_stop = base_stop
    except (TypeError, ValueError, IndexError):
        atr_stop = base_stop
    
    # Use tighter of the two (but cap at max)
    min_stop = entry_price * (1 - max_pct / 100)
    stop = max(atr_stop, min_stop)
    
    return stop


def backtest_params(df, target_pct, stop_pct, max_bars, rsi_lower=30, rsi_upper=70, 
                    require_volume=True, use_atr_stop=True, atr_mult=1.5):
    """Run backtest with specific parameters."""
    trades = []
    in_trade = False
    entry_price = 0
    entry_date = None
    stop_price = 0
    target_price = 0
    bars_held = 0
    
    df = calculate_indicators(df.copy())
    
    # Flatten multi-index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Extract scalar values
        try:
            high = float(row['High'].iloc[0]) if hasattr(row['High'], 'iloc') else float(row['High'])
            low = float(row['Low'].iloc[0]) if hasattr(row['Low'], 'iloc') else float(row['Low'])
            close = float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close'])
        except (TypeError, ValueError, IndexError):
            continue
        
        if in_trade:
            bars_held += 1
            
            # Check target
            if high >= target_price:
                pnl_pct = (target_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': row.name,
                    'entry_price': entry_price,
                    'exit_price': target_price,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'reason': 'target',
                    'outcome': 'WIN'
                })
                in_trade = False
                continue
            
            # Check stop loss
            if low <= stop_price:
                pnl_pct = (stop_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': row.name,
                    'entry_price': entry_price,
                    'exit_price': stop_price,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'reason': 'stop',
                    'outcome': 'LOSS'
                })
                in_trade = False
                continue
            
            # Check time exit
            if bars_held >= max_bars:
                pnl_pct = (close - entry_price) / entry_price * 100
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': row.name,
                    'entry_price': entry_price,
                    'exit_price': close,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'reason': 'time',
                    'outcome': 'WIN' if pnl_pct > 0 else 'LOSS'
                })
                in_trade = False
                continue
        else:
            # Look for entry signal
            signal = generate_signal(row, prev_row, rsi_lower, rsi_upper, require_volume)
            if signal == 1:
                entry_price = close
                entry_date = row.name
                
                if use_atr_stop:
                    stop_price = calculate_stop_loss(entry_price, row['ATR'], 
                                                     base_pct=stop_pct, atr_mult=atr_mult, 
                                                     max_pct=stop_pct + 1)
                else:
                    stop_price = entry_price * (1 - stop_pct / 100)
                
                target_price = entry_price * (1 + target_pct / 100)
                bars_held = 0
                in_trade = True
    
    return trades


def calculate_metrics(trades):
    """Calculate performance metrics from trades."""
    if not trades:
        return {'win_rate': 0, 'total_pnl': 0, 'avg_win': 0, 'avg_loss': 0, 
                'profit_factor': 0, 'trade_count': 0, 'expectancy': 0}
    
    wins = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    total_pnl = sum(t['pnl_pct'] for t in trades)
    avg_win = sum(t['pnl_pct'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl_pct'] for t in losses) / len(losses) if losses else 0
    
    gross_profit = sum(t['pnl_pct'] for t in wins)
    gross_loss = abs(sum(t['pnl_pct'] for t in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Expectancy per trade
    expectancy = total_pnl / len(trades) if trades else 0
    
    return {
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'trade_count': len(trades),
        'expectancy': expectancy
    }


def run_optimization():
    """Run parameter optimization across multiple tickers."""
    print("=" * 80)
    print("STRATEGY 5 PARAMETER OPTIMIZATION")
    print("=" * 80)
    print(f"\nFetching data for {len(TEST_TICKERS)} stocks...")
    
    # Fetch data for all tickers
    end_date = datetime.now()
    start_date = end_date - timedelta(days=400)  # ~1 year + buffer
    
    ticker_data = {}
    for ticker in TEST_TICKERS:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            # Flatten MultiIndex columns (yfinance returns ('Close', 'TICKER') format)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            if len(df) >= 200:
                ticker_data[ticker] = df
                print(f"  [OK] {ticker}: {len(df)} bars")
            else:
                print(f"  [SKIP] {ticker}: insufficient data ({len(df)} bars)")
        except Exception as e:
            print(f"  [FAIL] {ticker}: {e}")
    
    if not ticker_data:
        print("No data available for optimization!")
        return
    
    print(f"\nTesting {len(ticker_data)} tickers with valid data...")
    
    # Parameter combinations to test
    param_sets = [
        # Current Strategy 5 baseline
        {'name': 'Current S5', 'target': 5, 'stop': 3, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        
        # Lower target (more achievable)
        {'name': 'Lower Target 4%', 'target': 4, 'stop': 3, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        {'name': 'Lower Target 3%', 'target': 3, 'stop': 2, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        
        # Extended holding period
        {'name': 'Extended 15 bars', 'target': 5, 'stop': 3, 'bars': 15, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        {'name': 'Extended 20 bars', 'target': 5, 'stop': 3, 'bars': 20, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        
        # Tighter RSI range (more selective)
        {'name': 'Tight RSI 35-65', 'target': 5, 'stop': 3, 'bars': 10, 'rsi_lower': 35, 'rsi_upper': 65, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        
        # Wider stop loss
        {'name': 'Wider Stop 4%', 'target': 5, 'stop': 4, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 2.0},
        
        # Combined improvements
        {'name': 'OPTIMAL A: 4%/3%/15bars', 'target': 4, 'stop': 3, 'bars': 15, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        {'name': 'OPTIMAL B: 4%/4%/15bars', 'target': 4, 'stop': 4, 'bars': 15, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 2.0},
        {'name': 'OPTIMAL C: 3%/2%/20bars', 'target': 3, 'stop': 2, 'bars': 20, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': True, 'atr_mult': 1.5},
        
        # No volume filter
        {'name': 'No Volume Filter', 'target': 5, 'stop': 3, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': False, 'atr_stop': True, 'atr_mult': 1.5},
        
        # Fixed stop (no ATR)
        {'name': 'Fixed Stop (no ATR)', 'target': 5, 'stop': 3, 'bars': 10, 'rsi_lower': 30, 'rsi_upper': 70, 'vol': True, 'atr_stop': False, 'atr_mult': 1.5},
    ]
    
    # Run all parameter combinations
    results = []
    
    for params in param_sets:
        all_trades = []
        
        for ticker, df in ticker_data.items():
            trades = backtest_params(
                df, 
                target_pct=params['target'],
                stop_pct=params['stop'],
                max_bars=params['bars'],
                rsi_lower=params['rsi_lower'],
                rsi_upper=params['rsi_upper'],
                require_volume=params['vol'],
                use_atr_stop=params['atr_stop'],
                atr_mult=params['atr_mult']
            )
            all_trades.extend(trades)
        
        metrics = calculate_metrics(all_trades)
        metrics['name'] = params['name']
        metrics['params'] = params
        results.append(metrics)
    
    # Sort by expectancy (profit per trade)
    results.sort(key=lambda x: x['expectancy'], reverse=True)
    
    # Display results
    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS (sorted by expectancy)")
    print("=" * 80)
    print(f"{'Configuration':<25} {'WinRate':>8} {'Trades':>8} {'TotalP&L':>10} {'Expect':>8} {'PF':>6}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['name']:<25} {r['win_rate']:>7.1f}% {r['trade_count']:>8} {r['total_pnl']:>9.1f}% {r['expectancy']:>7.2f}% {r['profit_factor']:>6.2f}")
    
    # Best configuration
    best = results[0]
    print("\n" + "=" * 80)
    print("RECOMMENDED OPTIMAL CONFIGURATION")
    print("=" * 80)
    print(f"\n  Configuration: {best['name']}")
    print(f"  Target: {best['params']['target']}%")
    print(f"  Stop Loss: {best['params']['stop']}% (ATR mult: {best['params']['atr_mult']})")
    print(f"  Max Holding: {best['params']['bars']} bars")
    print(f"  RSI Range: {best['params']['rsi_lower']}-{best['params']['rsi_upper']}")
    print(f"  Volume Filter: {'Yes' if best['params']['vol'] else 'No'}")
    print(f"  ATR Stop: {'Yes' if best['params']['atr_stop'] else 'No'}")
    print(f"\n  Expected Results:")
    print(f"    Win Rate: {best['win_rate']:.1f}%")
    print(f"    Expectancy: {best['expectancy']:.2f}% per trade")
    print(f"    Profit Factor: {best['profit_factor']:.2f}")
    print(f"    Total P&L: {best['total_pnl']:.1f}% over {best['trade_count']} trades")
    
    # Compare with current
    current = next((r for r in results if r['name'] == 'Current S5'), None)
    if current and current != best:
        improvement = best['expectancy'] - current['expectancy']
        print(f"\n  Improvement over current: +{improvement:.2f}% per trade")
    
    print("\n" + "=" * 80)
    
    return results


if __name__ == "__main__":
    run_optimization()
