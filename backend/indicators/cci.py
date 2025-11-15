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
    - CCI < -100: Oversold ? Buy (+1)
    - CCI > 100: Overbought ? Sell (-1)
    - -100 ? CCI ? 100: Neutral (0)
    
    Confidence:
    - If CCI < -100: conf = min((abs(CCI) - 100) / 100, 1.0)
    - If CCI > 100: conf = min((CCI - 100) / 100, 1.0)
    - Otherwise: conf = 0
    """
    cci = calculate_cci(df)
    
    if cci < -100:
        vote = 1
        confidence = min((abs(cci) - 100) / 100, 1.0)
    elif cci > 100:
        vote = -1
        confidence = min((cci - 100) / 100, 1.0)
    else:
        vote = 0
        confidence = 0.0
    
    return {
        "name": "CCI",
        "value": round(cci, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
