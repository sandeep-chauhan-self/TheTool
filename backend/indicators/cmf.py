"""
Chaikin Money Flow Indicator
Period: 20
"""

def calculate_cmf(df, period=20):
    """Calculate Chaikin Money Flow"""
    mfm = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
    mfv = mfm * df['Volume']
    
    cmf = mfv.rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()
    
    return cmf.iloc[-1]

def vote_and_confidence(df):
    """
    Chaikin Money Flow voting logic:
    - CMF > 0: Buying pressure ? Buy (+1)
    - CMF < 0: Selling pressure ? Sell (-1)
    
    Confidence:
    - conf = min(abs(CMF) * 5, 1.0)
    """
    cmf = calculate_cmf(df)
    
    if cmf > 0:
        vote = 1
    elif cmf < 0:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(cmf) * 5, 1.0)
    
    return {
        "name": "Chaikin Money Flow",
        "value": round(cmf, 4),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volume"
    }
