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
