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
    - Price > SAR: Bullish → Buy (+1)
    - Price < SAR: Bearish → Sell (-1)
    
    Confidence (based on price-SAR separation):
    - Wider gap = stronger trend = higher confidence
    - Gap of 2% of price = 100% confidence
    - Narrow gap = trend may be reversing = lower confidence
    """
    psar, is_bull = calculate_psar(df)
    close_price = df['Close'].iloc[-1]
    
    if close_price > psar:
        vote = 1  # Bullish
    elif close_price < psar:
        vote = -1  # Bearish
    else:
        vote = 0  # Exactly at SAR (rare)
    
    # Confidence: 2% separation = 100% confidence
    # This gives meaningful confidence for most price-SAR relationships
    if close_price > 0:
        confidence = min(abs(close_price - psar) / (0.02 * close_price), 1.0)
    else:
        confidence = 0.0
    
    return {
        "name": "Parabolic SAR",
        "value": round(psar, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }
