"""
Parabolic SAR Indicator

Description:
Parabolic SAR (Stop and Reverse) is a trend-following indicator that provides
potential entry and exit points. It appears as dots above or below the price,
indicating potential reversal points.

Calculation:
SAR(i) = SAR(i-1) + AF � [EP - SAR(i-1)]
- SAR: Stop and Reverse price
- AF: Acceleration Factor (starts at 0.02, increments by 0.02, max 0.2)
- EP: Extreme Point (highest high in uptrend, lowest low in downtrend)

Parameters:
- af_start: Initial acceleration factor (default: 0.02)
- af_increment: AF increment on new extreme (default: 0.02)
- af_max: Maximum acceleration factor (default: 0.2)

Signals:
- Price crosses above SAR: Buy signal (bullish trend)
- Price crosses below SAR: Sell signal (bearish trend)

Performance:
- ISSUE_006: Numba JIT compilation (49x speedup)
- ISSUE_011: LRU caching with 1-hour TTL

Author: TheTool Trading System
Version: 1.1.0
"""

import numpy as np
from numba import jit
from cache import cached_indicator
from indicators.base import TrendIndicator

# PSAR Constants (MLRM-001)
PSAR_AF_START = 0.02
PSAR_AF_INCREMENT = 0.02
PSAR_AF_MAX = 0.2
PSAR_MIN_AF = 0.001
PSAR_MAX_AF = 1.0
PSAR_MIN_REQUIRED_ROWS = 2
PSAR_CONFIDENCE_MULTIPLIER = 0.03

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


@jit(nopython=True)
def _calculate_psar_jit(high, low, close, af_start=PSAR_AF_START, af_increment=PSAR_AF_INCREMENT, af_max=PSAR_AF_MAX):
    """
    JIT-compiled PSAR calculation for maximum performance
    
    Args:
        high: numpy array of high prices
        low: numpy array of low prices
        close: numpy array of close prices
        af_start: Initial acceleration factor
        af_increment: AF increment step
        af_max: Maximum AF value
    
    Returns:
        tuple: (psar_value, is_bullish)
    """
    n = len(high)
    psar = np.empty(n)
    psar[0] = close[0]
    
    bull = True
    af = af_start
    hp = high[0]
    lp = low[0]
    
    for i in range(1, n):
        if bull:
            psar[i] = psar[i-1] + af * (hp - psar[i-1])
            
            if low[i] < psar[i]:
                # Trend reversal to bearish
                bull = False
                psar[i] = hp
                lp = low[i]
                af = af_start
        else:
            psar[i] = psar[i-1] + af * (lp - psar[i-1])
            
            if high[i] > psar[i]:
                # Trend reversal to bullish
                bull = True
                psar[i] = lp
                hp = high[i]
                af = af_start
        
        # Update extreme point and acceleration factor
        if bull:
            if high[i] > hp:
                hp = high[i]
                af = min(af + af_increment, af_max)
        else:
            if low[i] < lp:
                lp = low[i]
                af = min(af + af_increment, af_max)
    
    return psar[n-1], bull


@cached_indicator('psar', ttl=3600)
def calculate_psar(df, af_start=PSAR_AF_START, af_increment=PSAR_AF_INCREMENT, af_max=PSAR_AF_MAX):
    """
    Calculate Parabolic SAR with JIT optimization and validation (MLRM-002)
    
    Args:
        df: pandas DataFrame with OHLC data
        af_start: Initial acceleration factor (default: 0.02)
        af_increment: AF increment (default: 0.02)
        af_max: Maximum AF (default: 0.2)
    
    Returns:
        tuple: (psar_value: float, is_bullish: bool)
    """
    # Validate inputs (MLRM-002)
    if df is None:
        raise ValueError("DataFrame cannot be None")
    if df.empty:
        raise ValueError("DataFrame cannot be empty")
    
    required_cols = ['High', 'Low', 'Close']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame must contain {missing} column(s)")
    
    for col in required_cols:
        if df[col].isnull().all():
            raise ValueError(f"'{col}' column cannot contain all NaN values")
    
    if len(df) < PSAR_MIN_REQUIRED_ROWS:
        raise ValueError(f"Insufficient data: need >= {PSAR_MIN_REQUIRED_ROWS} rows, got {len(df)}")
    
    # Validate AF parameters
    if not isinstance(af_start, (int, float)):
        raise TypeError(f"AF start must be numeric, got {type(af_start).__name__}")
    if af_start < PSAR_MIN_AF:
        raise ValueError(f"AF start must be >= {PSAR_MIN_AF}, got {af_start}")
    if af_start > PSAR_MAX_AF:
        raise ValueError(f"AF start must be <= {PSAR_MAX_AF}, got {af_start}")
    
    if not isinstance(af_increment, (int, float)):
        raise TypeError(f"AF increment must be numeric, got {type(af_increment).__name__}")
    if af_increment < PSAR_MIN_AF:
        raise ValueError(f"AF increment must be >= {PSAR_MIN_AF}, got {af_increment}")
    if af_increment > PSAR_MAX_AF:
        raise ValueError(f"AF increment must be <= {PSAR_MAX_AF}, got {af_increment}")
    
    if not isinstance(af_max, (int, float)):
        raise TypeError(f"AF max must be numeric, got {type(af_max).__name__}")
    if af_max < af_start:
        raise ValueError(f"AF max ({af_max}) must be >= AF start ({af_start})")
    if af_max > PSAR_MAX_AF:
        raise ValueError(f"AF max must be <= {PSAR_MAX_AF}, got {af_max}")
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    psar, is_bull = _calculate_psar_jit(high, low, close, af_start, af_increment, af_max)
    
    # Check for NaN/Inf (MLRM-002)
    if np.isnan(psar) or np.isinf(psar):
        raise ValueError("PSAR calculation resulted in NaN or Inf")
    
    return psar, is_bull


class PSARIndicator(TrendIndicator):
    """Parabolic SAR indicator implementation"""
    
    def __init__(self):
        super().__init__("Parabolic SAR", default_params={"af_start": PSAR_AF_START, "af_increment": PSAR_AF_INCREMENT, "af_max": PSAR_AF_MAX})
    
    def calculate(self, df, af_start: float = PSAR_AF_START, af_increment: float = PSAR_AF_INCREMENT, af_max: float = PSAR_AF_MAX) -> tuple:
        """Wrapper for calculate_psar (already cached)"""
        return calculate_psar(df, af_start, af_increment, af_max)
    
    def _get_vote(self, value: tuple, df) -> int:
        """Determine vote based on price vs PSAR (MLRM-001)"""
        psar, is_bull = value
        close_price = df['Close'].iloc[-1]
        
        if close_price > psar:
            return VOTE_BUY  # Bullish
        elif close_price < psar:
            return VOTE_SELL  # Bearish
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: tuple, df) -> float:
        """Calculate confidence based on distance from PSAR (MLRM-001)"""
        psar, is_bull = value
        close_price = df['Close'].iloc[-1]
        return min(abs(close_price - psar) / (PSAR_CONFIDENCE_MULTIPLIER * close_price), 1.0)


def vote_and_confidence(df):
    """Legacy function - calls PSARIndicator"""
    indicator = PSARIndicator()
    return indicator.vote_and_confidence(df)

