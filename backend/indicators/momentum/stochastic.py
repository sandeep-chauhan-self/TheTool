"""
Stochastic Oscillator Indicator
K period: 14, D period: 3, Smooth: 3

REFACTORED (ISSUE_008):
- Migrated to StochasticIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import MomentumIndicator
from cache import cached_indicator

# Stochastic Constants (MLRM-001)
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH_PERIOD = 3
STOCH_MIN_PERIOD = 2
STOCH_MAX_PERIOD = 100
STOCH_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5
STOCH_OVERSOLD_THRESHOLD = 20
STOCH_OVERBOUGHT_THRESHOLD = 80
STOCH_CONFIDENCE_DENOMINATOR = 20
STOCH_MULTIPLIER = 100

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class StochasticIndicator(MomentumIndicator):
    """Stochastic Oscillator indicator implementation"""
    
    def __init__(self):
        super().__init__("Stochastic", default_params={"k_period": STOCH_K_PERIOD, "d_period": STOCH_D_PERIOD, "smooth": STOCH_SMOOTH_PERIOD})
    
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
    
    def _validate_periods(self, k_period: int, d_period: int, smooth: int, df: pd.DataFrame) -> None:
        """Validate period parameters (MLRM-002)"""
        # K period validation
        if not isinstance(k_period, int):
            raise TypeError(f"K period must be an integer, got {type(k_period).__name__}")
        if k_period < STOCH_MIN_PERIOD:
            raise ValueError(f"K period must be >= {STOCH_MIN_PERIOD}, got {k_period}")
        if k_period > STOCH_MAX_PERIOD:
            raise ValueError(f"K period must be <= {STOCH_MAX_PERIOD}, got {k_period}")
        
        # D period validation
        if not isinstance(d_period, int):
            raise TypeError(f"D period must be an integer, got {type(d_period).__name__}")
        if d_period < STOCH_MIN_PERIOD:
            raise ValueError(f"D period must be >= {STOCH_MIN_PERIOD}, got {d_period}")
        if d_period > STOCH_MAX_PERIOD:
            raise ValueError(f"D period must be <= {STOCH_MAX_PERIOD}, got {d_period}")
        
        # Smooth period validation
        if not isinstance(smooth, int):
            raise TypeError(f"Smooth period must be an integer, got {type(smooth).__name__}")
        if smooth < STOCH_MIN_PERIOD:
            raise ValueError(f"Smooth period must be >= {STOCH_MIN_PERIOD}, got {smooth}")
        if smooth > STOCH_MAX_PERIOD:
            raise ValueError(f"Smooth period must be <= {STOCH_MAX_PERIOD}, got {smooth}")
        
        # Sufficient data check (use k_period as it's the largest)
        min_required_rows = int(k_period * STOCH_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for k_period {k_period}, got {len(df)}"
            )
    
    @cached_indicator('stochastic', ttl=3600)
    def calculate(self, df: pd.DataFrame, k_period: int = STOCH_K_PERIOD, d_period: int = STOCH_D_PERIOD, smooth: int = STOCH_SMOOTH_PERIOD) -> dict:
        """Calculate Stochastic Oscillator with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_periods(k_period, d_period, smooth, df)
        
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()
        
        # Avoid division by zero
        range_vals = high_max - low_min
        range_vals = range_vals.replace(0, np.nan)
        
        k = STOCH_MULTIPLIER * ((df['Close'] - low_min) / range_vals)
        k_smooth = k.rolling(window=smooth).mean()
        d = k_smooth.rolling(window=d_period).mean()
        
        k_val = float(k_smooth.iloc[-1])
        d_val = float(d.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(k_val) or np.isinf(k_val):
            raise ValueError("Stochastic %K calculation resulted in NaN or Inf")
        if np.isnan(d_val) or np.isinf(d_val):
            raise ValueError("Stochastic %D calculation resulted in NaN or Inf")
        
        return {
            'k': k_val,
            'd': d_val
        }
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on K value (MLRM-001)"""
        k = value['k']
        
        if k < STOCH_OVERSOLD_THRESHOLD:
            return VOTE_BUY  # Oversold
        elif k > STOCH_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL  # Overbought
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on distance from thresholds (MLRM-001)"""
        k = value['k']
        
        if k < STOCH_OVERSOLD_THRESHOLD:
            return min((STOCH_OVERSOLD_THRESHOLD - k) / STOCH_CONFIDENCE_DENOMINATOR, 1.0)
        elif k > STOCH_OVERBOUGHT_THRESHOLD:
            return min((k - STOCH_OVERBOUGHT_THRESHOLD) / STOCH_CONFIDENCE_DENOMINATOR, 1.0)
        return 0.0


# Backward compatibility
def calculate_stochastic(df, k_period=STOCH_K_PERIOD, d_period=STOCH_D_PERIOD, smooth=STOCH_SMOOTH_PERIOD):
    """Legacy function - calls StochasticIndicator"""
    indicator = StochasticIndicator()
    return indicator.calculate(df, k_period, d_period, smooth)


def vote_and_confidence(df):
    """Legacy function - calls StochasticIndicator"""
    indicator = StochasticIndicator()
    return indicator.vote_and_confidence(df)

