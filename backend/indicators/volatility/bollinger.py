"""
Bollinger Bands Indicator
Period: 20, Std Dev: 2

REFACTORED (ISSUE_008):
- Migrated to BollingerIndicator(VolatilityIndicator) class
"""

import pandas as pd
from indicators.base import VolatilityIndicator

BB_DEFAULT_PERIOD = 20
BB_DEFAULT_STD_DEV = 2
VOTE_BUY = 1
VOTE_SELL = -1
VOTE_NEUTRAL = 0


def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return {
        'upper': upper_band.iloc[-1],
        'middle': sma.iloc[-1],
        'lower': lower_band.iloc[-1]
    }

def vote_and_confidence(df):
    """
    Bollinger Bands voting logic:
    - Price < Lower Band: Oversold ? Buy (+1)
    - Price > Upper Band: Overbought ? Sell (-1)
    - Otherwise: Neutral (0)
    
    Confidence:
    - If price outside bands: conf = min(distance / band_width, 1.0)
    - Otherwise: conf = 0
    """
    bb_data = calculate_bollinger_bands(df)
    close_price = df['Close'].iloc[-1]
    band_width = bb_data['upper'] - bb_data['lower']
    
    if close_price < bb_data['lower']:
        vote = 1
        distance = bb_data['lower'] - close_price
        confidence = min(distance / band_width, 1.0)
    elif close_price > bb_data['upper']:
        vote = -1
        distance = close_price - bb_data['upper']
        confidence = min(distance / band_width, 1.0)
    else:
        vote = 0
        confidence = 0.0
    
    return {
        "name": "Bollinger Bands",
        "value": round(close_price, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volatility"
    }


class BollingerIndicator(VolatilityIndicator):
    """Bollinger Bands indicator implementation"""
    
    def __init__(self):
        super().__init__("Bollinger Bands", default_params={"period": BB_DEFAULT_PERIOD, "std_dev": BB_DEFAULT_STD_DEV})
    
    def calculate(self, df: pd.DataFrame, period: int = BB_DEFAULT_PERIOD, std_dev: float = BB_DEFAULT_STD_DEV) -> dict:
        """Calculate Bollinger Bands values"""
        return calculate_bollinger_bands(df, period, std_dev)
    
    def _get_vote(self, value: dict, df: pd.DataFrame) -> int:
        """Determine vote based on price position relative to bands"""
        close_price = df['Close'].iloc[-1]
        if close_price < value['lower']:
            return VOTE_BUY
        elif close_price > value['upper']:
            return VOTE_SELL
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
