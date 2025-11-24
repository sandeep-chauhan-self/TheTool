"""
Williams %R Indicator
Period: 14

REFACTORED (ISSUE_008):
- Migrated to WilliamsIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Maintains backward compatibility with legacy functions
"""

import pandas as pd
from indicators.base import MomentumIndicator

# Williams %R Constants
WILLIAMS_DEFAULT_PERIOD = 14
WILLIAMS_OVERSOLD_THRESHOLD = -80
WILLIAMS_OVERBOUGHT_THRESHOLD = -20
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_williams_r(df, period=14):
    """Calculate Williams %R indicator"""
    high_max = df['High'].rolling(window=period).max()
    low_min = df['Low'].rolling(window=period).min()
    
    williams_r = -100 * ((high_max - df['Close']) / (high_max - low_min))
    return williams_r.iloc[-1]

def vote_and_confidence(df):
    """
    Williams %R voting logic:
    - %R < -80: Oversold ? Buy (+1)
    - %R > -20: Overbought ? Sell (-1)
    - -80 ? %R ? -20: Neutral (0)
    
    Confidence:
    - If %R < -80: conf = (abs(%R) - 80) / 20
    - If %R > -20: conf = (20 - abs(%R)) / 20
    - Otherwise: conf = 0
    """
    williams_r = calculate_williams_r(df)
    
    if williams_r < -80:
        vote = 1
        confidence = (abs(williams_r) - 80) / 20
    elif williams_r > -20:
        vote = -1
        confidence = (20 - abs(williams_r)) / 20
    else:
        vote = 0
        confidence = 0.0
    
    confidence = min(confidence, 1.0)
    
    return {
        "name": "Williams %R",
        "value": round(williams_r, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }


class WilliamsIndicator(MomentumIndicator):
    """Williams %R indicator implementation"""
    
    def __init__(self):
        super().__init__("Williams %R", default_params={"period": WILLIAMS_DEFAULT_PERIOD})
    
    def calculate(self, df: pd.DataFrame, period: int = WILLIAMS_DEFAULT_PERIOD) -> float:
        """Calculate Williams %R value"""
        return calculate_williams_r(df, period)
    
    def _get_vote(self, value: float, df: pd.DataFrame) -> int:
        """Determine vote based on Williams %R value"""
        if value < WILLIAMS_OVERSOLD_THRESHOLD:
            return VOTE_BUY
        elif value > WILLIAMS_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: float, df: pd.DataFrame) -> float:
        """Calculate confidence based on %R extremeness"""
        if value < WILLIAMS_OVERSOLD_THRESHOLD:
            return min((abs(value) - 80) / 20, 1.0)
        elif value > WILLIAMS_OVERBOUGHT_THRESHOLD:
            return min((20 - abs(value)) / 20, 1.0)
        return 0.0
