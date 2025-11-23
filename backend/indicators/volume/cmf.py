"""
Chaikin Money Flow Indicator
Period: 20

REFACTORED (ISSUE_008):
- Migrated to CMFIndicator(VolumeIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import VolumeIndicator
from cache import cached_indicator

# CMF Constants (MLRM-001)
CMF_DEFAULT_PERIOD = 20
CMF_MIN_PERIOD = 2
CMF_MAX_PERIOD = 200
CMF_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
CMF_CONFIDENCE_MULTIPLIER = 5.0

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class CMFIndicator(VolumeIndicator):
    """Chaikin Money Flow indicator implementation"""
    
    def __init__(self):
        super().__init__("Chaikin Money Flow", default_params={"period": CMF_DEFAULT_PERIOD})
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure and content (MLRM-002)"""
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
        required_cols = ['High', 'Low', 'Close', 'Volume']
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
        if period < CMF_MIN_PERIOD:
            raise ValueError(f"Period must be >= {CMF_MIN_PERIOD}, got {period}")
        if period > CMF_MAX_PERIOD:
            raise ValueError(f"Period must be <= {CMF_MAX_PERIOD}, got {period}")
        
        min_required_rows = int(period * CMF_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    @cached_indicator('cmf', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = CMF_DEFAULT_PERIOD) -> float:
        """Calculate Chaikin Money Flow with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_period(period, df)
        
        # Avoid division by zero in MFM calculation
        range_vals = df['High'] - df['Low']
        range_vals = range_vals.replace(0, np.nan)  # Replace zeros with NaN to avoid div by zero
        
        mfm = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / range_vals
        mfv = mfm * df['Volume']
        
        # Compute rolling volume sum and guard against zero/near-zero division
        rolling_vol_sum = df['Volume'].rolling(window=period).sum()
        safe_vol_sum = rolling_vol_sum.replace(0, np.nan)  # Replace zeros with NaN to avoid Inf
        
        cmf = mfv.rolling(window=period).sum() / safe_vol_sum
        
        result = float(cmf.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(result) or np.isinf(result):
            raise ValueError("CMF calculation resulted in NaN or Inf")
        
        return result
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on CMF value (MLRM-001)"""
        if value > 0:
            return VOTE_BUY  # Buying pressure
        elif value < 0:
            return VOTE_SELL  # Selling pressure
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on CMF magnitude (MLRM-001)"""
        return min(abs(value) * CMF_CONFIDENCE_MULTIPLIER, 1.0)


# Backward compatibility
def calculate_cmf(df, period=CMF_DEFAULT_PERIOD):
    """Legacy function - calls CMFIndicator"""
    indicator = CMFIndicator()
    return indicator.calculate(df, period)


def vote_and_confidence(df):
    """Legacy function - calls CMFIndicator"""
    indicator = CMFIndicator()
    return indicator.vote_and_confidence(df)

