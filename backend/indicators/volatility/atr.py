"""
ATR (Average True Range) Indicator
Period: 14

REFACTORED (ISSUE_008):
- Migrated to ATRIndicator(VolatilityIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import VolatilityIndicator
from cache import cached_indicator

# ATR Constants (MLRM-001)
ATR_DEFAULT_PERIOD = 14
ATR_MIN_PERIOD = 2
ATR_MAX_PERIOD = 100
ATR_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
ATR_CONFIDENCE_MULTIPLIER = 0.05

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class ATRIndicator(VolatilityIndicator):
    """ATR indicator implementation"""
    
    def __init__(self):
        super().__init__("ATR", default_params={"period": ATR_DEFAULT_PERIOD})
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure and content (MLRM-002)"""
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
    
    def _validate_period(self, period: int, df: pd.DataFrame) -> None:
        """Validate period parameter (MLRM-002)"""
        if not isinstance(period, int):
            raise TypeError(f"Period must be an integer, got {type(period).__name__}")
        if period < ATR_MIN_PERIOD:
            raise ValueError(f"Period must be >= {ATR_MIN_PERIOD}, got {period}")
        if period > ATR_MAX_PERIOD:
            raise ValueError(f"Period must be <= {ATR_MAX_PERIOD}, got {period}")
        
        min_required_rows = int(period * ATR_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    @cached_indicator('atr', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = ATR_DEFAULT_PERIOD) -> float:
        """Calculate ATR indicator with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_period(period, df)
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        result = float(atr.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(result) or np.isinf(result):
            raise ValueError("ATR calculation resulted in NaN or Inf")
        
        return result
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """ATR is non-directional - always returns neutral (MLRM-001)"""
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on volatility level (MLRM-001)"""
        close_price = df['Close'].iloc[-1]
        return min(value / (ATR_CONFIDENCE_MULTIPLIER * close_price), 1.0)


# Backward compatibility
def calculate_atr(df, period=ATR_DEFAULT_PERIOD):
    """Legacy function - calls ATRIndicator"""
    indicator = ATRIndicator()
    return indicator.calculate(df, period)


def vote_and_confidence(df):
    """Legacy function - calls ATRIndicator"""
    indicator = ATRIndicator()
    return indicator.vote_and_confidence(df)

