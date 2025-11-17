"""
RSI (Relative Strength Index) Indicator
Period: 14

REFACTOR FIX (ISSUE_008): Migrated to IndicatorBase class
to eliminate code duplication and ensure consistent API.

MICRO-LEVEL REWRITE (PART 3A):
- Added magic number constants (MLRM-001)
- Added comprehensive boundary validation (MLRM-002)
- Enhanced error handling with descriptive messages
"""

import pandas as pd
import numpy as np
from indicators.base import MomentumIndicator
from cache import cached_indicator

# RSI Calculation Constants (MLRM-001: Magic Number Elimination)
RSI_DEFAULT_PERIOD = 14
RSI_MIN_PERIOD = 2
RSI_MAX_PERIOD = 200
RSI_MIN_REQUIRED_ROWS_MULTIPLIER = 1.5  # Need 1.5x period for accurate calculation

# RSI Threshold Constants
RSI_OVERSOLD_THRESHOLD = 30
RSI_OVERBOUGHT_THRESHOLD = 70
RSI_NEUTRAL_ZONE_LOWER = 40
RSI_NEUTRAL_ZONE_UPPER = 60

# RSI Confidence Calculation Constants
RSI_CONFIDENCE_DENOMINATOR = 30
RSI_MIN_VALUE = 0.0
RSI_MAX_VALUE = 100.0

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class RSIIndicator(MomentumIndicator):
    """RSI Indicator implementation with comprehensive validation"""
    
    def __init__(self):
        super().__init__("RSI", default_params={"period": RSI_DEFAULT_PERIOD})
    
    @cached_indicator('rsi', ttl=3600)
    def calculate(self, df: pd.DataFrame, period: int = RSI_DEFAULT_PERIOD) -> float:
        """
        Calculate RSI indicator with comprehensive validation
        
        Args:
            df: DataFrame with 'Close' column
            period: RSI calculation period (default: 14)
            
        Returns:
            float: RSI value between 0-100
            
        Raises:
            ValueError: If validation fails
            TypeError: If parameter types are invalid
        """
        # MLRM-002: Boundary Validation
        self._validate_dataframe(df)
        self._validate_period(period, df)
        
        # Calculation with proper edge case handling
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Handle division by zero (when loss is 0, RS is infinite, RSI = 100)
        rs = np.where(loss != 0, gain / loss, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        # Extract final value with validation
        final_rsi = rsi.iloc[-1] if hasattr(rsi, 'iloc') else rsi[-1]
        
        # Handle NaN/Inf cases
        if np.isnan(final_rsi) or np.isinf(final_rsi):
            raise ValueError("RSI calculation resulted in NaN or Inf - insufficient data quality")
        
        # Clamp to valid range (handle floating point errors)
        return float(np.clip(final_rsi, RSI_MIN_VALUE, RSI_MAX_VALUE))
    
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
    
    def _validate_period(self, period: int, df: pd.DataFrame) -> None:
        """Validate period parameter"""
        if not isinstance(period, int):
            raise TypeError(f"Period must be integer, got {type(period).__name__}")
        
        if period < RSI_MIN_PERIOD or period > RSI_MAX_PERIOD:
            raise ValueError(
                f"Period must be between {RSI_MIN_PERIOD} and {RSI_MAX_PERIOD}, got {period}"
            )
        
        min_required_rows = int(period * RSI_MIN_REQUIRED_ROWS_MULTIPLIER)
        if len(df) < min_required_rows:
            raise ValueError(
                f"Need at least {min_required_rows} rows for period {period}, got {len(df)}"
            )
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """
        RSI voting logic with named constants:
        - RSI < 30: Oversold → Buy (+1)
        - RSI > 70: Overbought → Sell (-1)
        - 30 ≤ RSI ≤ 70: Neutral (0)
        """
        if value < RSI_OVERSOLD_THRESHOLD:
            return VOTE_BUY
        elif value > RSI_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """
        Confidence based on distance from neutral zone:
        - If RSI < 30: conf = (30 - RSI) / 30
        - If RSI > 70: conf = (RSI - 70) / 30
        - Otherwise: conf = 0
        """
        if value < RSI_OVERSOLD_THRESHOLD:
            confidence = (RSI_OVERSOLD_THRESHOLD - value) / RSI_CONFIDENCE_DENOMINATOR
        elif value > RSI_OVERBOUGHT_THRESHOLD:
            confidence = (value - RSI_OVERBOUGHT_THRESHOLD) / RSI_CONFIDENCE_DENOMINATOR
        else:
            confidence = 0.0
        
        # Cap confidence at 1.0 (100%)
        return min(confidence, 1.0)


# Legacy function for backward compatibility
def calculate_rsi(df, period=RSI_DEFAULT_PERIOD):
    """Legacy function - use RSIIndicator class instead"""
    indicator = RSIIndicator()
    return indicator.calculate(df, period=period)


def vote_and_confidence(df):
    """Legacy function - use RSIIndicator class instead"""
    indicator = RSIIndicator()
    return indicator.vote_and_confidence(df)

