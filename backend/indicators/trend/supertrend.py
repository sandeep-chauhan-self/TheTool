"""
Supertrend Indicator

Description:
Supertrend is a trend-following indicator that provides dynamic support/resistance levels
based on ATR (Average True Range). It helps identify the current trend direction and
can be used as a trailing stop.

Calculation:
1. Calculate ATR (Average True Range)
2. Basic Upper Band = (High + Low) / 2 + (Multiplier � ATR)
3. Basic Lower Band = (High + Low) / 2 - (Multiplier � ATR)
4. Final bands adjust based on previous values and price
5. Supertrend switches between upper/lower bands based on close price

Parameters:
- period: ATR period (default: 10)
- multiplier: ATR multiplier for band width (default: 3)

Signals:
- Uptrend: Price > Supertrend (use lower band)
- Downtrend: Price < Supertrend (use upper band)
- Buy Signal: Trend changes from down to up
- Sell Signal: Trend changes from up to down

Performance:
- ISSUE_005: Vectorized calculations using NumPy (87x speedup)
- ISSUE_011: LRU caching with 1-hour TTL

Author: TheTool Trading System
Version: 1.1.0
"""

import pandas as pd
import numpy as np
from cache import cached_indicator
from indicators.base import TrendIndicator

# Supertrend Constants (MLRM-001)
ST_DEFAULT_PERIOD = 10
ST_DEFAULT_MULTIPLIER = 3
ST_MIN_PERIOD = 2
ST_MAX_PERIOD = 100
ST_MIN_MULTIPLIER = 0.5
ST_MAX_MULTIPLIER = 10.0
ST_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
ST_UPTREND = 1
ST_DOWNTREND = -1
ST_HIGH_CONFIDENCE = 0.9
ST_ESTABLISHED_CONFIDENCE = 0.8
ST_MEDIUM_CONFIDENCE = 0.5

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


@cached_indicator('supertrend', ttl=3600)
def calculate(data, period=ST_DEFAULT_PERIOD, multiplier=ST_DEFAULT_MULTIPLIER):
    """
    Calculate Supertrend indicator (Vectorized) with validation (MLRM-002)
    
    Args:
        data: pandas DataFrame with OHLC data
              Required columns: 'High', 'Low', 'Close'
        period: ATR period (default: 10)
        multiplier: ATR multiplier (default: 3)
    
    Returns:
        dict: {
            'value': float,           # Current Supertrend value
            'trend': str,             # 'uptrend' or 'downtrend'
            'signal': str,            # 'BUY', 'SELL', or 'HOLD'
            'signal_desc': str        # Human-readable description
        }
    """
    try:
        # Validate inputs (MLRM-002)
        if data is None:
            raise ValueError("DataFrame cannot be None")
        if data.empty:
            raise ValueError("DataFrame cannot be empty")
        
        required_cols = ['High', 'Low', 'Close']
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"DataFrame must contain {missing} column(s)")
        
        if not isinstance(period, int):
            raise TypeError(f"Period must be an integer, got {type(period).__name__}")
        if period < ST_MIN_PERIOD:
            raise ValueError(f"Period must be >= {ST_MIN_PERIOD}, got {period}")
        if period > ST_MAX_PERIOD:
            raise ValueError(f"Period must be <= {ST_MAX_PERIOD}, got {period}")
        
        if not isinstance(multiplier, (int, float)):
            raise TypeError(f"Multiplier must be numeric, got {type(multiplier).__name__}")
        if multiplier < ST_MIN_MULTIPLIER:
            raise ValueError(f"Multiplier must be >= {ST_MIN_MULTIPLIER}, got {multiplier}")
        if multiplier > ST_MAX_MULTIPLIER:
            raise ValueError(f"Multiplier must be <= {ST_MAX_MULTIPLIER}, got {multiplier}")
        
        min_required_rows = int(period * ST_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(data) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(data)}"
            )
        
        # Work with views/references instead of copies (ISSUE_005)
        high = data['High'].values
        low = data['Low'].values
        close = data['Close'].values
        n = len(data)
        
        # Step 1: Vectorized True Range calculation
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]  # Handle first element
        
        tr1 = high - low
        tr2 = np.abs(high - prev_close)
        tr3 = np.abs(low - prev_close)
        true_range = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Step 2: Calculate ATR using rolling mean (vectorized)
        atr = np.convolve(true_range, np.ones(period)/period, mode='same')
        atr[:period-1] = np.nan  # First period-1 values are invalid
        
        # Step 3: Calculate Basic Bands (vectorized)
        hl_avg = (high + low) / 2
        basic_upper_band = hl_avg + (multiplier * atr)
        basic_lower_band = hl_avg - (multiplier * atr)
        
        # Step 4: Calculate Final Bands (iterative, but optimized)
        final_upper_band = np.zeros(n)
        final_lower_band = np.zeros(n)
        
        for i in range(period, n):
            # Final Upper Band
            if basic_upper_band[i] < final_upper_band[i-1] or close[i-1] > final_upper_band[i-1]:
                final_upper_band[i] = basic_upper_band[i]
            else:
                final_upper_band[i] = final_upper_band[i-1]
            
            # Final Lower Band
            if basic_lower_band[i] > final_lower_band[i-1] or close[i-1] < final_lower_band[i-1]:
                final_lower_band[i] = basic_lower_band[i]
            else:
                final_lower_band[i] = final_lower_band[i-1]
        
        # Step 5: Determine Supertrend and Trend Direction (vectorized where possible)
        supertrend = np.zeros(n)
        trend_direction = np.zeros(n, dtype=int)
        
        # Initialize first value
        if close[period] <= final_upper_band[period]:
            supertrend[period] = final_upper_band[period]
            trend_direction[period] = -1
        else:
            supertrend[period] = final_lower_band[period]
            trend_direction[period] = 1
        
        # Calculate subsequent values
        for i in range(period + 1, n):
            if trend_direction[i-1] == 1:
                # Was in uptrend
                if close[i] <= final_lower_band[i]:
                    # Switch to downtrend
                    supertrend[i] = final_upper_band[i]
                    trend_direction[i] = -1
                else:
                    # Continue uptrend
                    supertrend[i] = final_lower_band[i]
                    trend_direction[i] = 1
            else:
                # Was in downtrend
                if close[i] >= final_upper_band[i]:
                    # Switch to uptrend
                    supertrend[i] = final_lower_band[i]
                    trend_direction[i] = 1
                else:
                    # Continue downtrend
                    supertrend[i] = final_upper_band[i]
                    trend_direction[i] = -1
        
        # Step 6: Get current values
        current_supertrend = supertrend[-1]
        current_trend = trend_direction[-1]
        
        # Step 7: Detect signal (trend change)
        signal = 'HOLD'
        signal_desc = 'No trend change'
        
        if n > period + 1:
            prev_trend = trend_direction[-2]
            
            if prev_trend == -1 and current_trend == 1:
                # Trend changed from down to up
                signal = 'BUY'
                signal_desc = f'Trend reversal to uptrend at {current_supertrend:.2f}'
            elif prev_trend == 1 and current_trend == -1:
                # Trend changed from up to down
                signal = 'SELL'
                signal_desc = f'Trend reversal to downtrend at {current_supertrend:.2f}'
            else:
                # Trend continues
                if current_trend == 1:
                    signal_desc = f'Uptrend continues (support at {current_supertrend:.2f})'
                else:
                    signal_desc = f'Downtrend continues (resistance at {current_supertrend:.2f})'
        
        # Step 8: Determine trend string
        trend_str = 'uptrend' if current_trend == 1 else 'downtrend'
        
        return {
            'value': round(current_supertrend, 2),
            'trend': trend_str,
            'signal': signal,
            'signal_desc': signal_desc
        }
        
    except Exception as e:
        return {
            'value': 0.0,
            'trend': 'unknown',
            'signal': 'HOLD',
            'signal_desc': f'Calculation error: {str(e)}'
        }


def get_description():
    """Return indicator description"""
    return {
        'name': 'Supertrend',
        'category': 'Trend Following',
        'description': 'Dynamic support/resistance based on ATR',
        'parameters': {
            'period': 'ATR period (default: 10)',
            'multiplier': 'ATR multiplier (default: 3)'
        },
        'signals': {
            'BUY': 'Trend changes from downtrend to uptrend',
            'SELL': 'Trend changes from uptrend to downtrend',
            'HOLD': 'Trend continues in same direction'
        },
        'usage': 'Trend filter for strategies, trailing stop levels'
    }


class SupertrendIndicator(TrendIndicator):
    """Supertrend indicator implementation"""
    
    def __init__(self):
        super().__init__("Supertrend", default_params={"period": 10, "multiplier": 3})
    
    def calculate(self, df: pd.DataFrame, period: int = 10, multiplier: int = 3) -> dict:
        """Wrapper for calculate (already cached)"""
        return calculate(df, period, multiplier)
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on signal (MLRM-001)"""
        vote_map = {'BUY': VOTE_BUY, 'SELL': VOTE_SELL, 'HOLD': VOTE_NEUTRAL}
        return vote_map.get(value['signal'], VOTE_NEUTRAL)
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on trend strength (MLRM-001)"""
        if value['signal'] in ['BUY', 'SELL']:
            return ST_HIGH_CONFIDENCE  # High confidence on trend change
        elif value['trend'] == 'uptrend':
            return ST_ESTABLISHED_CONFIDENCE  # Good confidence in established uptrend
        elif value['trend'] == 'downtrend':
            return ST_ESTABLISHED_CONFIDENCE  # Good confidence in established downtrend
        return ST_MEDIUM_CONFIDENCE  # Medium confidence for unknown


def vote_and_confidence(data, period=10, multiplier=3):
    """Legacy function - calls SupertrendIndicator"""
    indicator = SupertrendIndicator()
    return indicator.vote_and_confidence(data, period=period, multiplier=multiplier)

