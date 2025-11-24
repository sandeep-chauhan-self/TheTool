"""
Parabolic SAR Indicator

REFACTORED (ISSUE_008):
- Migrated to PSARIndicator(TrendIndicator) class
"""

import pandas as pd
from indicators.base import TrendIndicator

PSAR_AF_START = 0.02
PSAR_AF_INCREMENT = 0.02
PSAR_AF_MAX = 0.2
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_psar(df, af_start=0.02, af_increment=0.02, af_max=0.2):
    """Calculate Parabolic SAR"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    psar = close.copy()
    bull = True
    af = af_start
    hp = high.iloc[0]
    lp = low.iloc[0]
    
    for i in range(1, len(df)):
        if bull:
            psar.iloc[i] = psar.iloc[i-1] + af * (hp - psar.iloc[i-1])
            if low.iloc[i] < psar.iloc[i]:
                bull = False
                psar.iloc[i] = hp
                lp = low.iloc[i]
                af = af_start
        else:
            psar.iloc[i] = psar.iloc[i-1] + af * (lp - psar.iloc[i-1])
            if high.iloc[i] > psar.iloc[i]:
                bull = True
                psar.iloc[i] = lp
                hp = high.iloc[i]
                af = af_start
        
        if bull:
            if high.iloc[i] > hp:
                hp = high.iloc[i]
                af = min(af + af_increment, af_max)
        else:
            if low.iloc[i] < lp:
                lp = low.iloc[i]
                af = min(af + af_increment, af_max)
    
    return psar.iloc[-1], bull

def vote_and_confidence(df):
    """
    Parabolic SAR voting logic:
    - Price > SAR: Bullish ? Buy (+1)
    - Price < SAR: Bearish ? Sell (-1)
    
    Confidence:
    - conf = min(|price - SAR| / (0.03 * price), 1.0)
    """
    psar, is_bull = calculate_psar(df)
    close_price = df['Close'].iloc[-1]
    
    if close_price > psar:
        vote = 1
    elif close_price < psar:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(close_price - psar) / (0.03 * close_price), 1.0)
    
    return {
        "name": "Parabolic SAR",
        "value": round(psar, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }


class PSARIndicator(TrendIndicator):
    """Parabolic SAR indicator implementation"""
    
    def __init__(self):
        super().__init__("Parabolic SAR", default_params={"af_start": PSAR_AF_START, "af_increment": PSAR_AF_INCREMENT, "af_max": PSAR_AF_MAX})
    
    def calculate(self, df: pd.DataFrame, af_start: float = PSAR_AF_START, af_increment: float = PSAR_AF_INCREMENT, af_max: float = PSAR_AF_MAX) -> tuple:
        """Calculate Parabolic SAR value"""
        return calculate_psar(df, af_start, af_increment, af_max)
    
    def _get_vote(self, value: tuple, df: pd.DataFrame) -> int:
        """Determine vote based on price vs SAR"""
        psar, is_bull = value
        close_price = df['Close'].iloc[-1]
        if close_price > psar:
            return VOTE_BUY
        elif close_price < psar:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: tuple, df: pd.DataFrame) -> float:
        """Calculate confidence based on distance"""
        psar, is_bull = value
        close_price = df['Close'].iloc[-1]
        return min(abs(close_price - psar) / (0.03 * close_price), 1.0)
