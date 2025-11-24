"""
CCI (Commodity Channel Index) Indicator
Period: 20

REFACTORED (ISSUE_008):
- Migrated to CCIIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import MomentumIndicator
from cache import cached_indicator

# CCI Constants (MLRM-001)
CCI_DEFAULT_PERIOD = 20
CCI_MIN_PERIOD = 2
CCI_MAX_PERIOD = 200
CCI_CONSTANT = 0.015
CCI_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
CCI_OVERSOLD_THRESHOLD = -100
CCI_OVERBOUGHT_THRESHOLD = 100
CCI_CONFIDENCE_DENOMINATOR = 100

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class CCIIndicator(MomentumIndicator):
    """CCI indicator implementation"""
    
    def __init__(self):
        super().__init__("CCI", default_params={"period": CCI_DEFAULT_PERIOD})
    
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
        if period < CCI_MIN_PERIOD:
            raise ValueError(f"Period must be >= {CCI_MIN_PERIOD}, got {period}")
        if period > CCI_MAX_PERIOD:
            raise ValueError(f"Period must be <= {CCI_MAX_PERIOD}, got {period}")
        
        min_required_rows = int(period * CCI_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    @cached_indicator('cci', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = CCI_DEFAULT_PERIOD) -> float:
        """Calculate CCI indicator with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_period(period, df)
        
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
        
        cci = (tp - sma) / (CCI_CONSTANT * mad)
        result = float(cci.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(result) or np.isinf(result):
            raise ValueError("CCI calculation resulted in NaN or Inf")
        
        return result
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on CCI value (MLRM-001)"""
        if value < CCI_OVERSOLD_THRESHOLD:
            return VOTE_BUY  # Oversold
        elif value > CCI_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL  # Overbought
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on distance from thresholds (MLRM-001)"""
        if value < CCI_OVERSOLD_THRESHOLD:
            return min((abs(value) - abs(CCI_OVERSOLD_THRESHOLD)) / CCI_CONFIDENCE_DENOMINATOR, 1.0)
        elif value > CCI_OVERBOUGHT_THRESHOLD:
            return min((value - CCI_OVERBOUGHT_THRESHOLD) / CCI_CONFIDENCE_DENOMINATOR, 1.0)
        return 0.0


# Backward compatibility
def calculate_cci(df, period=CCI_DEFAULT_PERIOD):
    """Legacy function - calls CCIIndicator"""
    indicator = CCIIndicator()
    return indicator.calculate(df, period)


def vote_and_confidence(df):
    """Legacy function - calls CCIIndicator"""
    indicator = CCIIndicator()
    return indicator.vote_and_confidence(df)

