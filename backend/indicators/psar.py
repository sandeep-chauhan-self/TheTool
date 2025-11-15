"""
Parabolic SAR Indicator
"""

def calculate_psar(df, af_start=0.02, af_increment=0.02, af_max=0.2):
    """Calculate Parabolic SAR"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    psar = close.copy()
    bull = True
    af = af_start
    hp = high.iloc[0]
    lp = low.iloc[0]
    
    for i in range(1, len(df)):
        if bull:
            psar.iloc[i] = psar.iloc[i-1] + af * (hp - psar.iloc[i-1])
            if low.iloc[i] < psar.iloc[i]:
                bull = False
                psar.iloc[i] = hp
                lp = low.iloc[i]
                af = af_start
        else:
            psar.iloc[i] = psar.iloc[i-1] + af * (lp - psar.iloc[i-1])
            if high.iloc[i] > psar.iloc[i]:
                bull = True
                psar.iloc[i] = lp
                hp = high.iloc[i]
                af = af_start
        
        if bull:
            if high.iloc[i] > hp:
                hp = high.iloc[i]
                af = min(af + af_increment, af_max)
        else:
            if low.iloc[i] < lp:
                lp = low.iloc[i]
                af = min(af + af_increment, af_max)
    
    return psar.iloc[-1], bull

def vote_and_confidence(df):
    """
    Parabolic SAR voting logic:
    - Price > SAR: Bullish ? Buy (+1)
    - Price < SAR: Bearish ? Sell (-1)
    
    Confidence:
    - conf = min(|price - SAR| / (0.03 * price), 1.0)
    """
    psar, is_bull = calculate_psar(df)
    close_price = df['Close'].iloc[-1]
    
    if close_price > psar:
        vote = 1
    elif close_price < psar:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(close_price - psar) / (0.03 * close_price), 1.0)
    
    return {
        "name": "Parabolic SAR",
        "value": round(psar, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }
