"""
Williams %R Indicator
Period: 14
"""

def calculate_williams_r(df, period=14):
    """Calculate Williams %R indicator"""
    high_max = df['High'].rolling(window=period).max()
    low_min = df['Low'].rolling(window=period).min()
    
    williams_r = -100 * ((high_max - df['Close']) / (high_max - low_min))
    return williams_r.iloc[-1]

def vote_and_confidence(df):
    """
    Williams %R voting logic:
    - %R < -80: Oversold → Buy (+1)
    - %R > -20: Overbought → Sell (-1)
    - -80 ≤ %R ≤ -20: Neutral (0)
    
    Confidence (how certain the indicator is about its assessment):
    - %R at -50: 100% confident neutral (furthest from boundaries)
    - %R at -20 or -80: Low confidence (at boundary)
    - %R at 0 or -100: 100% confident in signal (extreme)
    """
    williams_r = calculate_williams_r(df)
    
    if williams_r < -80:
        vote = 1  # Buy (oversold)
        confidence = (abs(williams_r) - 80) / 20  # 0 at -80, 1.0 at -100
    elif williams_r > -20:
        vote = -1  # Sell (overbought)
        confidence = (20 - abs(williams_r)) / 20  # 0 at -20, 1.0 at 0
    else:
        vote = 0  # Neutral
        # Confidence highest at %R=-50 (furthest from -20 and -80)
        distance_from_boundary = min(abs(williams_r) - 20, 80 - abs(williams_r))  # 0-30 range
        confidence = distance_from_boundary / 30  # 0 at boundaries, 1.0 at -50
    
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "Williams %R",
        "value": round(williams_r, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
