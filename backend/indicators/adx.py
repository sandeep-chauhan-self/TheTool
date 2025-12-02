"""
ADX (Average Directional Index) Indicator
Period: 14
"""

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

import pandas as pd

def vote_and_confidence(df):
    """
    ADX voting logic:
    - DI+ > DI-: Bullish → Buy (+1)
    - DI+ < DI-: Bearish → Sell (-1)
    
    Confidence (based on trend strength AND DI separation):
    - ADX measures trend strength (0-100)
    - DI separation measures how clear the direction is
    - Combined for meaningful confidence
    """
    adx_data = calculate_adx(df)
    adx = adx_data['adx']
    di_plus = adx_data['di_plus']
    di_minus = adx_data['di_minus']
    
    if di_plus > di_minus:
        vote = 1  # Bullish
    elif di_plus < di_minus:
        vote = -1  # Bearish
    else:
        vote = 0  # No clear direction
    
    # ADX-based trend strength (0-100 scale)
    # ADX > 25 = strong trend, ADX > 50 = very strong
    adx_confidence = min(adx / 50, 1.0)  # 50+ ADX = 100% confidence
    
    # DI separation factor - how clear is the direction?
    di_total = di_plus + di_minus
    if di_total > 0:
        di_separation = abs(di_plus - di_minus) / di_total  # 0-1 range
    else:
        di_separation = 0.0
    
    # Combine: strong trend (ADX) + clear direction (DI separation)
    confidence = (adx_confidence * 0.6) + (di_separation * 0.4)
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "ADX",
        "value": round(adx, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }
