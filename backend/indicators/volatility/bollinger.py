"""
Bollinger Bands Indicator
Period: 20, Std Dev: 2

REFACTORED (ISSUE_008):
- Migrated to BollingerIndicator(VolatilityIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL

MICRO-LEVEL REWRITE (PART 3A):
- Added magic number constants (MLRM-001)
- Added comprehensive boundary validation (MLRM-002)
- Enhanced error handling
"""

import pandas as pd
import numpy as np
from indicators.base import VolatilityIndicator
from cache import cached_indicator

# Bollinger Bands Constants (MLRM-001)
BB_DEFAULT_PERIOD = 20
BB_DEFAULT_STD_DEV = 2
BB_MIN_PERIOD = 2
BB_MAX_PERIOD = 200
BB_MIN_STD_DEV = 0.5
BB_MAX_STD_DEV = 5.0
BB_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class BollingerIndicator(VolatilityIndicator):
    """Bollinger Bands indicator implementation"""
    
    def __init__(self):
        super().__init__("Bollinger Bands", default_params={"period": BB_DEFAULT_PERIOD, "std_dev": BB_DEFAULT_STD_DEV})
    
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
    
    def _validate_parameters(self, period: int, std_dev: float, df: pd.DataFrame) -> None:
        """Validate period and std_dev parameters (MLRM-002)"""
        # Period validation
        if not isinstance(period, int):
            raise TypeError(f"Period must be an integer, got {type(period).__name__}")
        if period < BB_MIN_PERIOD:
            raise ValueError(f"Period must be >= {BB_MIN_PERIOD}, got {period}")
        if period > BB_MAX_PERIOD:
            raise ValueError(f"Period must be <= {BB_MAX_PERIOD}, got {period}")
        
        # Std deviation validation
        if not isinstance(std_dev, (int, float)):
            raise TypeError(f"Std dev must be numeric, got {type(std_dev).__name__}")
        if std_dev < BB_MIN_STD_DEV:
            raise ValueError(f"Std dev must be >= {BB_MIN_STD_DEV}, got {std_dev}")
        if std_dev > BB_MAX_STD_DEV:
            raise ValueError(f"Std dev must be <= {BB_MAX_STD_DEV}, got {std_dev}")
        
        # Sufficient data check
        min_required_rows = int(period * BB_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Insufficient data: need >= {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    @cached_indicator('bollinger', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = BB_DEFAULT_PERIOD, std_dev: float = BB_DEFAULT_STD_DEV) -> dict:
        """Calculate Bollinger Bands with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        self._validate_parameters(period, std_dev, df)
        
        # Calculate bands
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        # Extract final values with NaN/Inf handling
        upper_val = float(upper_band.iloc[-1])
        middle_val = float(sma.iloc[-1])
        lower_val = float(lower_band.iloc[-1])
        
        # Check for NaN/Inf
        if np.isnan(upper_val) or np.isinf(upper_val):
            raise ValueError("Upper band calculation resulted in NaN or Inf")
        if np.isnan(middle_val) or np.isinf(middle_val):
            raise ValueError("Middle band (SMA) calculation resulted in NaN or Inf")
        if np.isnan(lower_val) or np.isinf(lower_val):
            raise ValueError("Lower band calculation resulted in NaN or Inf")
        
        return {
            'upper': upper_val,
            'middle': middle_val,
            'lower': lower_val
        }
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on price vs bands (MLRM-001)"""
        close_price = df['Close'].iloc[-1]
        
        if close_price < value['lower']:
            return VOTE_BUY  # Oversold
        elif close_price > value['upper']:
            return VOTE_SELL  # Overbought
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on distance from bands"""
        close_price = df['Close'].iloc[-1]
        band_width = value['upper'] - value['lower']
        
        if close_price < value['lower']:
            distance = value['lower'] - close_price
            return min(distance / band_width, 1.0)
        elif close_price > value['upper']:
            distance = close_price - value['upper']
            return min(distance / band_width, 1.0)
        return 0.0


# Backward compatibility
def calculate_bollinger_bands(df, period=BB_DEFAULT_PERIOD, std_dev=BB_DEFAULT_STD_DEV):
    """Legacy function - calls BollingerIndicator"""
    indicator = BollingerIndicator()
    return indicator.calculate(df, period, std_dev)


def vote_and_confidence(df):
    """Legacy function - calls BollingerIndicator"""
    indicator = BollingerIndicator()
    return indicator.vote_and_confidence(df)

