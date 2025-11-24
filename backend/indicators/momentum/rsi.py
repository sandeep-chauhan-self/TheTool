"""
RSI (Relative Strength Index) Indicator
Period: 14

REFACTORED (ISSUE_008):
- Migrated to RSIIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Maintains backward compatibility with legacy functions
"""

import pandas as pd
import numpy as np
from indicators.base import MomentumIndicator

# RSI Constants (MLRM-001)
RSI_DEFAULT_PERIOD = 14
RSI_MIN_PERIOD = 2
RSI_MAX_PERIOD = 200
RSI_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
RSI_OVERSOLD_THRESHOLD = 30
RSI_OVERBOUGHT_THRESHOLD = 70
RSI_WEAK_CONFIDENCE = 0.0
RSI_CONFIDENCE_DIVISOR = 30
RSI_STRONG_DIVISOR = 50

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_rsi(df, period=RSI_DEFAULT_PERIOD):
    """Calculate RSI indicator"""
    # Validate inputs
    if df is None or df.empty:
        raise ValueError("DataFrame cannot be None or empty")
    if 'Close' not in df.columns:
        raise ValueError("DataFrame must contain 'Close' column")
    if period < RSI_MIN_PERIOD:
        raise ValueError(f"Period must be >= {RSI_MIN_PERIOD}, got {period}")
    if period > RSI_MAX_PERIOD:
        raise ValueError(f"Period must be <= {RSI_MAX_PERIOD}, got {period}")
    
    min_required_rows = int(period * RSI_MIN_REQUIRED_ROWS_MULTIPLIER)
    if len(df) < min_required_rows:
        raise ValueError(f"Insufficient data: need >= {min_required_rows} rows, got {len(df)}")
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def vote_and_confidence(df):
    """
    RSI voting logic:
    - RSI < 30: Oversold ? Buy (+1)
    - RSI > 70: Overbought ? Sell (-1)
    - 30 ? RSI ? 70: Neutral (0)
    
    Confidence:
    - If RSI < 30: conf = (30 - RSI) / 30
    - If RSI > 70: conf = (RSI - 70) / 30
    - Otherwise: conf = 0
    """
    rsi = calculate_rsi(df)
    
    if rsi < RSI_OVERSOLD_THRESHOLD:
        vote = VOTE_BUY
        confidence = (RSI_OVERSOLD_THRESHOLD - rsi) / RSI_OVERSOLD_THRESHOLD
    elif rsi > RSI_OVERBOUGHT_THRESHOLD:
        vote = VOTE_SELL
        confidence = (rsi - RSI_OVERBOUGHT_THRESHOLD) / (100 - RSI_OVERBOUGHT_THRESHOLD)
    else:
        vote = VOTE_NEUTRAL
        confidence = RSI_WEAK_CONFIDENCE
    
    confidence = min(confidence, 1.0)  # Cap at 1.0
    
    return {
        "name": "RSI",
        "value": round(rsi, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }


class RSIIndicator(MomentumIndicator):
    """RSI indicator implementation"""
    
    def __init__(self):
        super().__init__("RSI", default_params={"period": RSI_DEFAULT_PERIOD})
    
    def calculate(self, df: pd.DataFrame, period: int = RSI_DEFAULT_PERIOD) -> float:
        """Calculate RSI value"""
        return calculate_rsi(df, period)
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on RSI value"""
        if value < RSI_OVERSOLD_THRESHOLD:
            return VOTE_BUY
        elif value > RSI_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on RSI extremeness"""
        if value < RSI_OVERSOLD_THRESHOLD:
            return min((RSI_OVERSOLD_THRESHOLD - value) / RSI_OVERSOLD_THRESHOLD, 1.0)
        elif value > RSI_OVERBOUGHT_THRESHOLD:
            return min((value - RSI_OVERBOUGHT_THRESHOLD) / (100 - RSI_OVERBOUGHT_THRESHOLD), 1.0)
        return RSI_WEAK_CONFIDENCE

