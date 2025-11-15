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
    - EMA50 > EMA200: Golden Cross ? Buy (+1)
    - EMA50 < EMA200: Death Cross ? Sell (-1)
    
    Confidence:
    - conf = min(|EMA50 - EMA200| / EMA200, 0.1) * 10
    """
    ema_data = calculate_ema_crossover(df)
    ema_fast = ema_data['ema_fast']
    ema_slow = ema_data['ema_slow']
    
    if ema_fast > ema_slow:
        vote = 1
    elif ema_fast < ema_slow:
        vote = -1
    else:
        vote = 0
    
    confidence = min(abs(ema_fast - ema_slow) / ema_slow, 0.1) * 10
    
    return {
        "name": "EMA Crossover",
        "value": round(ema_data['crossover'], 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "trend"
    }
