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
    - Always returns vote = 0 (neutral)
    
    Confidence (how reliable is the ATR reading):
    - ATR confidence is based on volatility consistency
    - Moderate volatility (2-3% of price) = highest confidence
    - Very low or very high volatility = lower confidence (unusual conditions)
    """
    atr = calculate_atr(df)
    close_price = df['Close'].iloc[-1]
    
    vote = 0  # ATR is non-directional
    
    # ATR as % of price
    if close_price > 0:
        atr_pct = atr / close_price
        
        # Optimal ATR range is 1-4% of price (normal market conditions)
        # Below 1% = unusually low volatility
        # Above 4% = unusually high volatility
        # Both extremes = less reliable readings
        
        if atr_pct < 0.01:  # < 1%
            # Very low volatility - less reliable
            confidence = atr_pct / 0.01  # 0 at 0%, 1.0 at 1%
        elif atr_pct > 0.04:  # > 4%
            # Very high volatility - less reliable
            confidence = max(0.5, 1.0 - ((atr_pct - 0.04) / 0.04))  # Decreases from 1.0, min 0.5
        else:
            # Normal volatility range - high confidence
            confidence = 1.0
    else:
        confidence = 0.0
    
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "ATR",
        "value": round(atr, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volatility"
    }
