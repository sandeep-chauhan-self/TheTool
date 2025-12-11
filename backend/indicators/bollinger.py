"""
Bollinger Bands Indicator
Period: 20, Std Dev: 2
"""

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return {
        'upper': upper_band.iloc[-1],
        'middle': sma.iloc[-1],
        'lower': lower_band.iloc[-1]
    }

def vote_and_confidence(df):
    """
    Bollinger Bands voting logic:
    - Price < Lower Band: Oversold → Buy (+1)
    - Price > Upper Band: Overbought → Sell (-1)
    - Otherwise: Neutral (0)
    
    Confidence (how certain the indicator is about its assessment):
    - Price at middle band: 100% confident neutral
    - Price at upper/lower band: Low confidence (at boundary)
    - Price far outside bands: High confidence in signal
    """
    bb_data = calculate_bollinger_bands(df)
    close_price = df['Close'].iloc[-1]
    band_width = bb_data['upper'] - bb_data['lower']
    middle_band = bb_data['middle']
    half_width = band_width / 2
    
    if close_price < bb_data['lower']:
        vote = 1  # Buy (below lower band)
        distance = bb_data['lower'] - close_price
        confidence = min(distance / half_width, 1.0)  # More extreme = higher confidence
    elif close_price > bb_data['upper']:
        vote = -1  # Sell (above upper band)
        distance = close_price - bb_data['upper']
        confidence = min(distance / half_width, 1.0)  # More extreme = higher confidence
    else:
        vote = 0  # Neutral (inside bands)
        # Confidence highest at middle band (furthest from both boundaries)
        distance_from_middle = abs(close_price - middle_band)
        # 0 at boundaries (half_width from middle), 1.0 at middle (0 from middle)
        confidence = 1.0 - (distance_from_middle / half_width) if half_width > 0 else 0.5
    
    confidence = min(max(confidence, 0.0), 1.0)
    
    return {
        "name": "Bollinger Bands",
        "value": round(close_price, 2),
        "vote": vote,
        "confidence": round(confidence, 2),
        "category": "volatility"
    }
