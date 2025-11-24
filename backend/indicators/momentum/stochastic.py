"""
Stochastic Oscillator Indicator
K period: 14, D period: 3, Smooth: 3

REFACTORED (ISSUE_008):
- Migrated to StochasticIndicator(MomentumIndicator) class
- Uses IndicatorBase abstract class pattern
- Maintains backward compatibility with legacy functions
"""

import pandas as pd
from indicators.base import MomentumIndicator

# Stochastic Constants
STOCHASTIC_K_PERIOD = 14
STOCHASTIC_D_PERIOD = 3
STOCHASTIC_SMOOTH = 3
STOCHASTIC_OVERSOLD_THRESHOLD = 20
STOCHASTIC_OVERBOUGHT_THRESHOLD = 80
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_stochastic(df, k_period=14, d_period=3, smooth=3):
    """Calculate Stochastic Oscillator"""
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    k_smooth = k.rolling(window=smooth).mean()
    d = k_smooth.rolling(window=d_period).mean()
    
    return {
        'k': k_smooth.iloc[-1],
        'd': d.iloc[-1]
    }

def vote_and_confidence(df):
    """
    Stochastic voting logic:
    - K < 20: Oversold ? Buy (+1)
    - K > 80: Overbought ? Sell (-1)
    - 20 ? K ? 80: Neutral (0)
    
    Confidence:
    - If K < 20: conf = (20 - K) / 20
    - If K > 80: conf = (K - 80) / 20
    - Otherwise: conf = 0
    """
    stoch_data = calculate_stochastic(df)
    k = stoch_data['k']
    
    if k < 20:
        vote = 1
        confidence = (20 - k) / 20
    elif k > 80:
        vote = -1
        confidence = (k - 80) / 20
    else:
        vote = 0
        confidence = 0.0
    
    confidence = min(confidence, 1.0)
    
    return {
        "name": "Stochastic",
        "value": round(k, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }


class StochasticIndicator(MomentumIndicator):
    """Stochastic Oscillator indicator implementation"""
    
    def __init__(self):
        super().__init__("Stochastic", default_params={"k_period": STOCHASTIC_K_PERIOD, "d_period": STOCHASTIC_D_PERIOD, "smooth": STOCHASTIC_SMOOTH})
    
    def calculate(self, df: pd.DataFrame, k_period: int = STOCHASTIC_K_PERIOD, d_period: int = STOCHASTIC_D_PERIOD, smooth: int = STOCHASTIC_SMOOTH) -> dict:
        """Calculate Stochastic values"""
        return calculate_stochastic(df, k_period, d_period, smooth)
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on K value"""
        k = value['k']
        if k < STOCHASTIC_OVERSOLD_THRESHOLD:
            return VOTE_BUY
        elif k > STOCHASTIC_OVERBOUGHT_THRESHOLD:
            return VOTE_SELL
        return VOTE_NEUTRAL
    
    def _get_confidence(self, value: dict, df: pd.DataFrame) -> float:
        """Calculate confidence based on K extremeness"""
        k = value['k']
        if k < STOCHASTIC_OVERSOLD_THRESHOLD:
            return min((STOCHASTIC_OVERSOLD_THRESHOLD - k) / STOCHASTIC_OVERSOLD_THRESHOLD, 1.0)
        elif k > STOCHASTIC_OVERBOUGHT_THRESHOLD:
            return min((k - STOCHASTIC_OVERBOUGHT_THRESHOLD) / (100 - STOCHASTIC_OVERBOUGHT_THRESHOLD), 1.0)
        return 0.0
