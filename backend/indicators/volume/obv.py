"""
OBV (On-Balance Volume) Indicator

REFACTORED (ISSUE_008):
- Migrated to OBVIndicator(VolumeIndicator) class
"""

import pandas as pd
from indicators.base import VolumeIndicator

VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_obv(df):
    """Calculate OBV indicator"""
    obv = [0]
    
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    
    return obv[-1], obv[-2] if len(obv) > 1 else 0

def vote_and_confidence(df):
    """
    OBV voting logic:
    - OBV increasing & price increasing: Buy (+1)
    - OBV decreasing & price decreasing: Sell (-1)
    - Divergence or flat: Neutral (0)
    
    Confidence:
    - conf = min(|OBV_change| / (0.2 * avg_volume), 1.0)
    """
    obv_current, obv_prev = calculate_obv(df)
    price_current = df['Close'].iloc[-1]
    price_prev = df['Close'].iloc[-2]
    avg_volume = df['Volume'].mean()
    
    obv_change = obv_current - obv_prev
    price_change = price_current - price_prev
    
    if obv_change > 0 and price_change > 0:
        vote = 1
    elif obv_change < 0 and price_change < 0:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(obv_change) / (0.2 * avg_volume * len(df)), 1.0) if avg_volume > 0 else 0
    
    return {
        "name": "OBV",
        "value": round(obv_current, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volume"
    }


class OBVIndicator(VolumeIndicator):
    """OBV indicator implementation"""
    
    def __init__(self):
        super().__init__("OBV")
    
    def calculate(self, df: pd.DataFrame) -> tuple:
        """Calculate OBV value"""
        return calculate_obv(df)
    
    def _get_vote(self, value: tuple, df: pd.DataFrame) -> int:
        """Determine vote based on OBV vs price movement"""
        obv_current, obv_prev = value
        price_current = df['Close'].iloc[-1]
        price_prev = df['Close'].iloc[-2]
        
        obv_change = obv_current - obv_prev
        price_change = price_current - price_prev
        
        if obv_change > 0 and price_change > 0:
            return VOTE_BUY
        elif obv_change < 0 and price_change < 0:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: tuple, df: pd.DataFrame) -> float:
        """Calculate confidence based on OBV change"""
        obv_current, obv_prev = value
        avg_volume = df['Volume'].mean()
        obv_change = obv_current - obv_prev
        return min(abs(obv_change) / (0.2 * avg_volume * len(df)), 1.0) if avg_volume > 0 else 0.0
