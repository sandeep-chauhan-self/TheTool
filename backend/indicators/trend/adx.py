"""
ADX (Average Directional Index) Indicator
Period: 14

REFACTORED (ISSUE_008):
- Migrated to ADXIndicator(TrendIndicator) class
"""

import pandas as pd
from indicators.base import TrendIndicator

ADX_DEFAULT_PERIOD = 14
ADX_STRONG_TREND_THRESHOLD = 25
ADX_WEAK_TREND_THRESHOLD = 20
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_adx(df, period=14):
    """Calculate ADX indicator"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    dm_plus = high.diff()
    dm_minus = -low.diff()
    
    dm_plus[dm_plus < 0] = 0
    dm_minus[dm_minus < 0] = 0
    dm_plus[(dm_plus < dm_minus)] = 0
    dm_minus[(dm_minus < dm_plus)] = 0
    
    # Smoothed TR and DM
    tr_smooth = tr.rolling(window=period).sum()
    dm_plus_smooth = dm_plus.rolling(window=period).sum()
    dm_minus_smooth = dm_minus.rolling(window=period).sum()
    
    # Directional Indicators
    di_plus = 100 * (dm_plus_smooth / tr_smooth)
    di_minus = 100 * (dm_minus_smooth / tr_smooth)
    
    # ADX
    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
    adx = dx.rolling(window=period).mean()
    
    return {
        'adx': adx.iloc[-1],
        'di_plus': di_plus.iloc[-1],
        'di_minus': di_minus.iloc[-1]
    }

def vote_and_confidence(df):
    """
    ADX voting logic:
    - DI+ > DI-: Bullish ? Buy (+1)
    - DI+ < DI-: Bearish ? Sell (-1)
    
    Confidence:
    - If ADX > 25: Strong trend ? conf = min(ADX / 50, 1.0)
    - If ADX < 20: Weak trend ? conf = 0.3
    - Otherwise: conf = ADX / 40
    """
    adx_data = calculate_adx(df)
    adx = adx_data['adx']
    di_plus = adx_data['di_plus']
    di_minus = adx_data['di_minus']
    
    if di_plus > di_minus:
        vote = 1
    elif di_plus < di_minus:
        vote = -1
    else:
        vote = 0
    
    if adx > 25:
        confidence = min(adx / 50, 1.0)
    elif adx < 20:
        confidence = 0.3
    else:
        confidence = adx / 40
    
    return {
        "name": "ADX",
        "value": round(adx, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }


class ADXIndicator(TrendIndicator):
    """ADX indicator implementation"""
    
    def __init__(self):
        super().__init__("ADX", default_params={"period": ADX_DEFAULT_PERIOD})
    
    def calculate(self, df: pd.DataFrame, period: int = ADX_DEFAULT_PERIOD) -> dict:
        """Calculate ADX values"""
        return calculate_adx(df, period)
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on DI+ vs DI-"""
        if value['di_plus'] > value['di_minus']:
            return VOTE_BUY
        elif value['di_plus'] < value['di_minus']:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on ADX strength"""
        adx = value['adx']
        if adx > ADX_STRONG_TREND_THRESHOLD:
            return min(adx / 50, 1.0)
        elif adx < ADX_WEAK_TREND_THRESHOLD:
            return 0.3
        return adx / 40
