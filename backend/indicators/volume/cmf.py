"""
Chaikin Money Flow Indicator
Period: 20

REFACTORED (ISSUE_008):
- Migrated to CMFIndicator(VolumeIndicator) class
"""

import pandas as pd
from indicators.base import VolumeIndicator

CMF_DEFAULT_PERIOD = 20
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_cmf(df, period=20):
    """Calculate Chaikin Money Flow"""
    mfm = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
    mfv = mfm * df['Volume']
    
    cmf = mfv.rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()
    
    return cmf.iloc[-1]

def vote_and_confidence(df):
    """
    Chaikin Money Flow voting logic:
    - CMF > 0: Buying pressure ? Buy (+1)
    - CMF < 0: Selling pressure ? Sell (-1)
    
    Confidence:
    - conf = min(abs(CMF) * 5, 1.0)
    """
    cmf = calculate_cmf(df)
    
    if cmf > 0:
        vote = 1
    elif cmf < 0:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(cmf) * 5, 1.0)
    
    return {
        "name": "Chaikin Money Flow",
        "value": round(cmf, 4),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volume"
    }


class CMFIndicator(VolumeIndicator):
    """Chaikin Money Flow indicator implementation"""
    
    def __init__(self):
        super().__init__("Chaikin Money Flow", default_params={"period": CMF_DEFAULT_PERIOD})
    
    def calculate(self, df: pd.DataFrame, period: int = CMF_DEFAULT_PERIOD) -> float:
        """Calculate CMF value"""
        return calculate_cmf(df, period)
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on CMF sign"""
        if value > 0:
            return VOTE_BUY
        elif value < 0:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on CMF magnitude"""
        return min(abs(value) * 5, 1.0)
