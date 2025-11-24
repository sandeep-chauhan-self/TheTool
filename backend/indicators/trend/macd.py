"""
MACD (Moving Average Convergence Divergence) Indicator

REFACTORED (ISSUE_008):
- Migrated to MACDIndicator(TrendIndicator) class
"""

import pandas as pd
from indicators.base import TrendIndicator

MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }

def vote_and_confidence(df):
    """
    MACD voting logic:
    - Histogram > 0: Bullish ? Buy (+1)
    - Histogram < 0: Bearish ? Sell (-1)
    
    Confidence:
    - conf = min(|histogram| / (0.02 * close_price), 1.0)
    """
    macd_data = calculate_macd(df)
    histogram = macd_data['histogram']
    close_price = df['Close'].iloc[-1]
    
    if histogram > 0:
        vote = 1
    elif histogram < 0:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(histogram) / (0.02 * close_price), 1.0)
    
    return {
        "name": "MACD",
        "value": round(histogram, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }


class MACDIndicator(TrendIndicator):
    """MACD indicator implementation"""
    
    def __init__(self):
        super().__init__("MACD", default_params={"fast": MACD_FAST_PERIOD, "slow": MACD_SLOW_PERIOD, "signal": MACD_SIGNAL_PERIOD})
    
    def calculate(self, df: pd.DataFrame, fast: int = MACD_FAST_PERIOD, slow: int = MACD_SLOW_PERIOD, signal: int = MACD_SIGNAL_PERIOD) -> dict:
        """Calculate MACD values"""
        return calculate_macd(df, fast, slow, signal)
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on histogram"""
        histogram = value['histogram']
        if histogram > 0:
            return VOTE_BUY
        elif histogram < 0:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on histogram magnitude"""
        histogram = value['histogram']
        close_price = df['Close'].iloc[-1]
        return min(abs(histogram) / (0.02 * close_price), 1.0)
