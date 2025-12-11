"""
Stochastic Oscillator Indicator
K period: 14, D period: 3, Smooth: 3
"""

def calculate_stochastic(df, k_period=14, d_period=3, smooth=3):
    """Calculate Stochastic Oscillator"""
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    k_smooth = k.rolling(window=smooth).mean()
    d = k_smooth.rolling(window=d_period).mean()
    
    return {
        'k': k_smooth.iloc[-1],
        'd': d.iloc[-1]
    }

def vote_and_confidence(df):
    """
    Stochastic voting logic:
    - K < 20: Oversold → Buy (+1)
    - K > 80: Overbought → Sell (-1)
    - 20 ≤ K ≤ 80: Neutral (0)
    
    Confidence (how certain the indicator is about its assessment):
    - K at 50: 100% confident neutral (furthest from boundaries)
    - K at 20 or 80: Low confidence (at boundary)
    - K at 0 or 100: 100% confident in signal (extreme)
    """
    stoch_data = calculate_stochastic(df)
    k = stoch_data['k']
    
    if k < 20:
        vote = 1  # Buy (oversold)
        confidence = (20 - k) / 20  # 0 at K=20, 1.0 at K=0
    elif k > 80:
        vote = -1  # Sell (overbought)
        confidence = (k - 80) / 20  # 0 at K=80, 1.0 at K=100
    else:
        vote = 0  # Neutral
        # Confidence highest at K=50 (furthest from boundaries)
        distance_from_boundary = min(k - 20, 80 - k)  # 0-30 range
        confidence = distance_from_boundary / 30  # 0 at boundaries, 1.0 at K=50
    
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "Stochastic",
        "value": round(k, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "momentum"
    }
