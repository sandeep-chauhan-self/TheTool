"""
EMA Crossover Indicator
Fast: 50, Slow: 200

REFACTORED (ISSUE_008):
- Migrated to EMAIndicator(TrendIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import TrendIndicator
from cache import cached_indicator

# EMA Constants (MLRM-001)
EMA_FAST_PERIOD = 50
EMA_SLOW_PERIOD = 200
EMA_MIN_PERIOD = 2
EMA_MAX_PERIOD = 500
EMA_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
EMA_CONFIDENCE_MULTIPLIER = 10.0
EMA_CONFIDENCE_DIVISOR = 0.1

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class EMAIndicator(TrendIndicator):
    """EMA Crossover indicator implementation"""
    
    def __init__(self):
        super().__init__("EMA Crossover", default_params={"fast": EMA_FAST_PERIOD, "slow": EMA_SLOW_PERIOD})
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure and content (MLRM-002)"""
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")
        if df['Close'].isnull().all():
            raise ValueError("'Close' column cannot contain all NaN values")
    
    def _validate_periods(self, fast: int, slow: int, df: pd.DataFrame) -> None:
        """Validate period parameters (MLRM-002)"""
        # Fast period validation
        if not isinstance(fast, int):
            raise TypeError(f"Fast period must be an integer, got {type(fast).__name__}")
        if fast < EMA_MIN_PERIOD:
            raise ValueError(f"Fast period must be >= {EMA_MIN_PERIOD}, got {fast}")
        if fast > EMA_MAX_PERIOD:
            raise ValueError(f"Fast period must be <= {EMA_MAX_PERIOD}, got {fast}")
        
        # Slow period validation
        if not isinstance(slow, int):
            raise TypeError(f"Slow period must be an integer, got {type(slow).__name__}")
        if slow < EMA_MIN_PERIOD:
            raise ValueError(f"Slow period must be >= {EMA_MIN_PERIOD}, got {slow}")
        if slow > EMA_MAX_PERIOD:
            raise ValueError(f"Slow period must be <= {EMA_MAX_PERIOD}, got {slow}")
        
        # Logical check: fast < slow
        if fast >= slow:
            raise ValueError(f"Fast period ({fast}) must be less than slow period ({slow})")
        
        # Sufficient data check
        min_required_rows = int(slow * EMA_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for slow period {slow}, got {len(df)}"
            )
    
    @cached_indicator('ema', ttl=3600)
    def calculate(self, df: pd.DataFrame, fast: int = EMA_FAST_PERIOD, slow: int = EMA_SLOW_PERIOD) -> dict:
        """Calculate EMA crossover with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_periods(fast, slow, df)
        
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        fast_val = float(ema_fast.iloc[-1])
        slow_val = float(ema_slow.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(fast_val) or np.isinf(fast_val):
            raise ValueError("Fast EMA calculation resulted in NaN or Inf")
        if np.isnan(slow_val) or np.isinf(slow_val):
            raise ValueError("Slow EMA calculation resulted in NaN or Inf")
        
        return {
            'ema_fast': fast_val,
            'ema_slow': slow_val,
            'crossover': fast_val - slow_val
        }
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on EMA crossover (MLRM-001)"""
        ema_fast = value['ema_fast']
        ema_slow = value['ema_slow']
        
        if ema_fast > ema_slow:
            return VOTE_BUY  # Golden cross
        elif ema_fast < ema_slow:
            return VOTE_SELL  # Death cross
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on EMA separation (MLRM-001)"""
        ema_fast = value['ema_fast']
        ema_slow = value['ema_slow']
        
        return min(abs(ema_fast - ema_slow) / ema_slow, EMA_CONFIDENCE_DIVISOR) * EMA_CONFIDENCE_MULTIPLIER


# Backward compatibility
def calculate_ema_crossover(df, fast=EMA_FAST_PERIOD, slow=EMA_SLOW_PERIOD):
    """Legacy function - calls EMAIndicator"""
    indicator = EMAIndicator()
    return indicator.calculate(df, fast, slow)


def vote_and_confidence(df):
    """Legacy function - calls EMAIndicator"""
    indicator = EMAIndicator()
    return indicator.vote_and_confidence(df)

