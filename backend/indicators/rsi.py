"""
RSI (Relative Strength Index) Indicator
Period: 14
"""

def calculate_rsi(df, period=14):
    """Calculate RSI indicator"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def vote_and_confidence(df):
    """
    RSI voting logic:
    - RSI < 30: Oversold → Buy (+1)
    - RSI > 70: Overbought → Sell (-1)
    - 30 ≤ RSI ≤ 70: Neutral (0)
    
    Confidence (how certain the indicator is about its assessment):
    - Measures distance from decision boundaries
    - RSI at 50: 100% confident neutral (furthest from any boundary)
    - RSI at 30 or 70: Lower confidence (at boundary, could go either way)
    - RSI at 0 or 100: 100% confident in signal (extreme reading)
    """
    rsi = calculate_rsi(df)
    
    if rsi < 30:
        vote = 1  # Buy (oversold)
        # Confidence increases as RSI gets more extreme (closer to 0)
        confidence = (30 - rsi) / 30  # 0 at RSI=30, 1.0 at RSI=0
    elif rsi > 70:
        vote = -1  # Sell (overbought)
        # Confidence increases as RSI gets more extreme (closer to 100)
        confidence = (rsi - 70) / 30  # 0 at RSI=70, 1.0 at RSI=100
    else:
        vote = 0  # Neutral
        # Confidence is highest at RSI=50 (furthest from boundaries)
        # Distance from nearest boundary (30 or 70)
        distance_from_boundary = min(rsi - 30, 70 - rsi)  # 0-20 range
        confidence = distance_from_boundary / 20  # 0 at boundaries, 1.0 at RSI=50
    
    confidence = min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]
    
    return {
        "name": "RSI",
        "value": round(rsi, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
