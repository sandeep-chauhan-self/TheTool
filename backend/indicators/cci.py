"""
CCI (Commodity Channel Index) Indicator
Period: 20
"""

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
    - CCI < -100: Oversold → Buy (+1)
    - CCI > 100: Overbought → Sell (-1)
    - -100 ≤ CCI ≤ 100: Neutral (0)
    
    Confidence (how certain the indicator is about its assessment):
    - CCI at 0: 100% confident neutral (furthest from boundaries)
    - CCI at ±100: Low confidence (at boundary)
    - CCI at ±200+: 100% confident in signal (extreme)
    """
    cci = calculate_cci(df)
    
    if cci < -100:
        vote = 1  # Buy (oversold)
        confidence = min((abs(cci) - 100) / 100, 1.0)  # 0 at -100, 1.0 at -200
    elif cci > 100:
        vote = -1  # Sell (overbought)
        confidence = min((cci - 100) / 100, 1.0)  # 0 at 100, 1.0 at 200
    else:
        vote = 0  # Neutral
        # Confidence highest at CCI=0 (furthest from ±100 boundaries)
        distance_from_boundary = 100 - abs(cci)  # 0-100 range
        confidence = distance_from_boundary / 100  # 0 at boundaries, 1.0 at CCI=0
    
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "CCI",
        "value": round(cci, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
