"""
CCI (Commodity Channel Index) Indicator
Period: 20

REFACTORED (ISSUE_008):
- Migrated to CCIIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Maintains backward compatibility with legacy functions
"""

import pandas as pd
from indicators.base import MomentumIndicator

# CCI Constants
CCI_DEFAULT_PERIOD = 20
CCI_OVERSOLD_THRESHOLD = -100
CCI_OVERBOUGHT_THRESHOLD = 100
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_cci(df, period=20):
    """Calculate CCI indicator"""
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
    
    cci = (tp - sma) / (0.015 * mad)
    return cci.iloc[-1]

def vote_and_confidence(df):
    """
    CCI voting logic:
    - CCI < -100: Oversold ? Buy (+1)
    - CCI > 100: Overbought ? Sell (-1)
    - -100 ? CCI ? 100: Neutral (0)
    
    Confidence:
    - If CCI < -100: conf = min((abs(CCI) - 100) / 100, 1.0)
    - If CCI > 100: conf = min((CCI - 100) / 100, 1.0)
    - Otherwise: conf = 0
    """
    cci = calculate_cci(df)
    
    if cci < -100:
        vote = 1
        confidence = min((abs(cci) - 100) / 100, 1.0)
    elif cci > 100:
        vote = -1
        confidence = min((cci - 100) / 100, 1.0)
    else:
        vote = 0
        confidence = 0.0
    
    return {
        "name": "CCI",
        "value": round(cci, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }


class CCIIndicator(MomentumIndicator):
    """CCI indicator implementation"""
    
    def __init__(self):
        super().__init__("CCI", default_params={"period": CCI_DEFAULT_PERIOD})
    
    def calculate(self, df: pd.DataFrame, period: int = CCI_DEFAULT_PERIOD) -> float:
        """Calculate CCI value"""
        return calculate_cci(df, period)
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on CCI value"""
        if value < CCI_OVERSOLD_THRESHOLD:
            return VOTE_BUY
        elif value > CCI_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on CCI extremeness"""
        if value < CCI_OVERSOLD_THRESHOLD:
            return min((abs(value) - 100) / 100, 1.0)
        elif value > CCI_OVERBOUGHT_THRESHOLD:
            return min((value - 100) / 100, 1.0)
        return 0.0
