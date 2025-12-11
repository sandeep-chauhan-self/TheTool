"""
OBV (On-Balance Volume) Indicator

REFACTORED (ISSUE_008):
- Migrated to OBVIndicator(VolumeIndicator) class
- Uses IndicatorBase abstract class pattern
- Backward compatible with legacy functions

PERFORMANCE (ISSUE_011):
- Added result caching with 1-hour TTL
"""

import pandas as pd
import numpy as np
from indicators.base import VolumeIndicator
from cache import cached_indicator

# OBV Constants (MLRM-001)
OBV_MIN_REQUIRED_ROWS = 2
OBV_CONFIDENCE_MULTIPLIER = 0.2

# Vote Constants
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


class OBVIndicator(VolumeIndicator):
    """OBV indicator implementation"""
    
    def __init__(self):
        super().__init__("OBV", default_params={})
    
    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate DataFrame structure and content (MLRM-002)"""
        if df is None:
            raise ValueError("DataFrame cannot be None")
        if df.empty:
            raise ValueError("DataFrame cannot be empty")
        required_cols = ['Close', 'Volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"DataFrame must contain {missing} column(s)")
        for col in required_cols:
            if df[col].isnull().all():
                raise ValueError(f"'{col}' column cannot contain all NaN values")
        if len(df) < OBV_MIN_REQUIRED_ROWS:
            raise ValueError(f"Insufficient data: need >= {OBV_MIN_REQUIRED_ROWS} rows, got {len(df)}")
    
    @cached_indicator('obv', ttl=3600)
    def calculate(self, df: pd.DataFrame) -> tuple:
        """Calculate OBV indicator with validation (MLRM-002)"""
        # Validate inputs
        self._validate_dataframe(df)
        
        obv = [0]
        
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        obv_current = float(obv[-1])
        obv_prev = float(obv[-2] if len(obv) > 1 else 0)
        
        # Check for NaN/Inf
        if np.isnan(obv_current) or np.isinf(obv_current):
            raise ValueError("OBV calculation resulted in NaN or Inf")
        
        return obv_current, obv_prev
    
    def _get_vote(self, value: tuple, df: pd.DataFrame) -> int:
        """Determine vote based on OBV and price direction (MLRM-001)
        
        OBV voting logic:
        - OBV increasing & price increasing: Buy (+1) - confirming uptrend
        - OBV decreasing & price decreasing: Sell (-1) - confirming downtrend  
        - Divergence or flat: Neutral (0) - conflicting signals or no movement
        """
        obv_current, obv_prev = value
        price_current = df['Close'].iloc[-1]
        price_prev = df['Close'].iloc[-2]
        
        obv_change = obv_current - obv_prev
        price_change = price_current - price_prev
        
        if obv_change > 0 and price_change > 0:
            return VOTE_BUY
        elif obv_change < 0 and price_change < 0:
            return VOTE_SELL
        else:
            return VOTE_NEUTRAL
    
    def _get_confidence(self, value: tuple, df: pd.DataFrame) -> float:
        """Calculate confidence based on OBV-price alignment (MLRM-001)
        
        Confidence reflects how strongly OBV confirms (or diverges from) price:
        - Strong confirmation (same direction, large OBV move): High confidence
        - Divergence (opposite directions): Lower confidence, but still meaningful
          because divergence itself is a signal worth noting
        - Flat/no change: Moderate confidence (market consolidating)
        """
        obv_current, obv_prev = value
        price_current = df['Close'].iloc[-1]
        price_prev = df['Close'].iloc[-2]
        avg_volume = df['Volume'].mean()
        
        obv_change = obv_current - obv_prev
        price_change = price_current - price_prev
        
        if avg_volume <= 0:
            return 0.5  # Default moderate confidence
        
        # Base confidence on OBV magnitude relative to average volume
        obv_magnitude = min(abs(obv_change) / (OBV_CONFIDENCE_MULTIPLIER * avg_volume), 1.0)
        
        # Check alignment between OBV and price
        if (obv_change > 0 and price_change > 0) or (obv_change < 0 and price_change < 0):
            # Confirmation - OBV and price moving same direction
            confidence = 0.5 + (obv_magnitude * 0.5)  # 50-100% range
        elif (obv_change > 0 and price_change < 0) or (obv_change < 0 and price_change > 0):
            # Divergence - still meaningful, indicates potential reversal
            confidence = 0.3 + (obv_magnitude * 0.4)  # 30-70% range
        else:
            # No clear movement
            confidence = 0.5  # Moderate confidence
        
        return min(max(confidence, 0.0), 1.0)


# Backward compatibility
def calculate_obv(df):
    """Legacy function - calls OBVIndicator"""
    indicator = OBVIndicator()
    return indicator.calculate(df)


def vote_and_confidence(df):
    """Legacy function - calls OBVIndicator"""
    indicator = OBVIndicator()
    return indicator.vote_and_confidence(df)

