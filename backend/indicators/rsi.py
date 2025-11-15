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
    - RSI < 30: Oversold ? Buy (+1)
    - RSI > 70: Overbought ? Sell (-1)
    - 30 ? RSI ? 70: Neutral (0)
    
    Confidence:
    - If RSI < 30: conf = (30 - RSI) / 30
    - If RSI > 70: conf = (RSI - 70) / 30
    - Otherwise: conf = 0
    """
    rsi = calculate_rsi(df)
    
    if rsi < 30:
        vote = 1
        confidence = (30 - rsi) / 30
    elif rsi > 70:
        vote = -1
        confidence = (rsi - 70) / 30
    else:
        vote = 0
        confidence = 0.0
    
    confidence = min(confidence, 1.0)  # Cap at 1.0
    
    return {
        "name": "RSI",
        "value": round(rsi, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
