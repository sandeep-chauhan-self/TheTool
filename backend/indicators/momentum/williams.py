"""
Williams %R Indicator
Period: 14

REFACTORED (ISSUE_008):
- Migrated to WilliamsIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import MomentumIndicator
from cache import cached_indicator

# Williams %R Constants (MLRM-001)
WILLIAMS_DEFAULT_PERIOD = 14
WILLIAMS_MIN_PERIOD = 2
WILLIAMS_MAX_PERIOD = 100
WILLIAMS_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
WILLIAMS_OVERSOLD_THRESHOLD = -80
WILLIAMS_OVERBOUGHT_THRESHOLD = -20
WILLIAMS_CONFIDENCE_DENOMINATOR = 20
WILLIAMS_MULTIPLIER = -100

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class WilliamsIndicator(MomentumIndicator):
    """Williams %R indicator implementation"""
    
    def __init__(self):
        super().__init__("Williams %R", default_params={"period": WILLIAMS_DEFAULT_PERIOD})
    
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
        if period < WILLIAMS_MIN_PERIOD:
            raise ValueError(f"Period must be >= {WILLIAMS_MIN_PERIOD}, got {period}")
        if period > WILLIAMS_MAX_PERIOD:
            raise ValueError(f"Period must be <= {WILLIAMS_MAX_PERIOD}, got {period}")
        
        min_required_rows = int(period * WILLIAMS_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    @cached_indicator('williams', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = WILLIAMS_DEFAULT_PERIOD) -> float:
        """Calculate Williams %R indicator with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_period(period, df)
        
        high_max = df['High'].rolling(window=period).max()
        low_min = df['Low'].rolling(window=period).min()
        
        # Avoid division by zero
        range_vals = high_max - low_min
        range_vals = range_vals.replace(0, np.nan)
        
        williams_r = WILLIAMS_MULTIPLIER * ((high_max - df['Close']) / range_vals)
        result = float(williams_r.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(result) or np.isinf(result):
            raise ValueError("Williams %R calculation resulted in NaN or Inf")
        
        return result
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on Williams %R value (MLRM-001)"""
        if value < WILLIAMS_OVERSOLD_THRESHOLD:
            return VOTE_BUY  # Oversold
        elif value > WILLIAMS_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL  # Overbought
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on distance from thresholds (MLRM-001)"""
        if value < WILLIAMS_OVERSOLD_THRESHOLD:
            return min((abs(value) - abs(WILLIAMS_OVERSOLD_THRESHOLD)) / WILLIAMS_CONFIDENCE_DENOMINATOR, 1.0)
        elif value > WILLIAMS_OVERBOUGHT_THRESHOLD:
            return min((abs(WILLIAMS_OVERBOUGHT_THRESHOLD) - abs(value)) / WILLIAMS_CONFIDENCE_DENOMINATOR, 1.0)
        return 0.0


# Backward compatibility
def calculate_williams_r(df, period=WILLIAMS_DEFAULT_PERIOD):
    """Legacy function - calls WilliamsIndicator"""
    indicator = WilliamsIndicator()
    return indicator.calculate(df, period)


def vote_and_confidence(df):
    """Legacy function - calls WilliamsIndicator"""
    indicator = WilliamsIndicator()
    return indicator.vote_and_confidence(df)

