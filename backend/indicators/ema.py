"""
EMA Crossover Indicator
Fast: 50, Slow: 200
"""

def calculate_ema_crossover(df, fast=50, slow=200):
    """Calculate EMA crossover"""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    
    return {
        'ema_fast': ema_fast.iloc[-1],
        'ema_slow': ema_slow.iloc[-1],
        'crossover': ema_fast.iloc[-1] - ema_slow.iloc[-1]
    }

def vote_and_confidence(df):
    """
    EMA Crossover voting logic:
    - EMA50 > EMA200: Golden Cross → Buy (+1)
    - EMA50 < EMA200: Death Cross → Sell (-1)
    
    Confidence (how certain based on EMA separation):
    - Wider gap = stronger trend = higher confidence
    - Gap of 5%+ of price = 100% confidence
    - Tiny gap = low confidence (trend just starting or ending)
    """
    ema_data = calculate_ema_crossover(df)
    ema_fast = ema_data['ema_fast']
    ema_slow = ema_data['ema_slow']
    
    if ema_fast > ema_slow:
        vote = 1  # Bullish (golden cross)
    elif ema_fast < ema_slow:
        vote = -1  # Bearish (death cross)
    else:
        vote = 0  # Exactly equal (rare)
    
    # Confidence based on % separation between EMAs
    # 5% separation = 100% confidence, 0% = 0% confidence
    if ema_slow > 0:
        separation_pct = abs(ema_fast - ema_slow) / ema_slow
        confidence = min(separation_pct / 0.05, 1.0)  # 5% = max confidence
    else:
        confidence = 0.0
    
    return {
        "name": "EMA Crossover",
        "value": round(ema_data['crossover'], 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }
