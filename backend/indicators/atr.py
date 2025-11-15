"""
ATR (Average True Range) Indicator
Period: 14
"""

def calculate_atr(df, period=14):
    """Calculate ATR indicator"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr.iloc[-1]

import pandas as pd

def vote_and_confidence(df):
    """
    ATR voting logic:
    - ATR itself doesn't provide directional signal
    - Used for stop/target calculation
    - Always returns vote = 0
    
    Confidence:
    - Based on volatility level
    - conf = min(ATR / (0.05 * close_price), 1.0)
    """
    atr = calculate_atr(df)
    close_price = df['Close'].iloc[-1]
    
    vote = 0
    confidence = min(atr / (0.05 * close_price), 1.0)
    
    return {
        "name": "ATR",
        "value": round(atr, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volatility"
    }
