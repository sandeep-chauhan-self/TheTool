"""
MACD (Moving Average Convergence Divergence) Indicator

REFACTORED (ISSUE_008):
- Migrated to MACDIndicator(TrendIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL

MICRO-LEVEL REWRITE (PART 3A):
- Added magic number constants (MLRM-001)
- Added comprehensive boundary validation (MLRM-002)
- Enhanced error handling with descriptive messages
"""

import pandas as pd
import numpy as np
from indicators.base import TrendIndicator
from cache import cached_indicator

# MACD Calculation Constants (MLRM-001)
MACD_FAST_PERIOD = 12
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9
MACD_MIN_PERIOD = 2
MACD_MAX_PERIOD = 200
MACD_MIN_REQUIRED_ROWS_MULTIPLIER = 2.0  # Need 2x slow period

# MACD Confidence Constants
MACD_CONFIDENCE_MULTIPLIER = 0.02  # 2% of close price
MACD_HISTOGRAM_THRESHOLD = 0.0

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class MACDIndicator(TrendIndicator):
    """MACD indicator implementation with comprehensive validation"""
    
    def __init__(self):
        super().__init__("MACD", default_params={
            "fast": MACD_FAST_PERIOD,
            "slow": MACD_SLOW_PERIOD,
            "signal": MACD_SIGNAL_PERIOD
        })
    
    @cached_indicator('macd', ttl=3600)
    def calculate(self, df: pd.DataFrame, fast: int = MACD_FAST_PERIOD, 
                  slow: int = MACD_SLOW_PERIOD, signal: int = MACD_SIGNAL_PERIOD) -> dict:
        """
        Calculate MACD indicator with comprehensive validation
        
        Args:
            df: DataFrame with 'Close' column
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            dict: MACD values (macd, signal, histogram)
            
        Raises:
            ValueError: If validation fails
            TypeError: If parameter types are invalid
        """
        # MLRM-002: Boundary Validation
        self._validate_dataframe(df)
        self._validate_periods(fast, slow, signal, df)
        
        # Calculation
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # Extract values with validation
        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        histogram_val = histogram.iloc[-1]
        
        # Handle NaN/Inf cases
        if any(np.isnan(v) or np.isinf(v) for v in [macd_val, signal_val, histogram_val]):
            raise ValueError("MACD calculation resulted in NaN or Inf - insufficient data quality")
        
        return {
            'macd': float(macd_val),
            'signal': float(signal_val),
            'histogram': float(histogram_val)
        }
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure and content"""
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must contain 'Close' column")
        if df['Close'].isnull().all():
            raise ValueError("'Close' column cannot contain all NaN values")
    
    def _validate_periods(self, fast: int, slow: int, signal: int, df: pd.DataFrame) -> None:
        """Validate period parameters"""
        for period, name in [(fast, 'fast'), (slow, 'slow'), (signal, 'signal')]:
            if not isinstance(period, int):
                raise TypeError(f"{name} period must be integer, got {type(period).__name__}")
            if period < MACD_MIN_PERIOD or period > MACD_MAX_PERIOD:
                raise ValueError(
                    f"{name} period must be between {MACD_MIN_PERIOD} and {MACD_MAX_PERIOD}, got {period}"
                )
        
        if fast >= slow:
            raise ValueError(f"Fast period ({fast}) must be less than slow period ({slow})")
        
        min_required_rows = int(slow * MACD_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Need at least {min_required_rows} rows for slow period {slow}, got {len(df)}"
            )
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on histogram"""
        histogram = value['histogram']
        if histogram > MACD_HISTOGRAM_THRESHOLD:
            return VOTE_BUY
        elif histogram < -MACD_HISTOGRAM_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on histogram strength"""
        histogram = value['histogram']
        close_price = df['Close'].iloc[-1]
        confidence = abs(histogram) / (MACD_CONFIDENCE_MULTIPLIER * close_price)
        return min(confidence, 1.0)


# Backward compatibility
def calculate_macd(df, fast=MACD_FAST_PERIOD, slow=MACD_SLOW_PERIOD, signal=MACD_SIGNAL_PERIOD):
    """Legacy function - calls MACDIndicator"""
    indicator = MACDIndicator()
    return indicator.calculate(df, fast, slow, signal)


def vote_and_confidence(df):
    """Legacy function - calls MACDIndicator"""
    indicator = MACDIndicator()
    return indicator.vote_and_confidence(df)

