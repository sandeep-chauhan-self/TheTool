"""
Volatility Indicators Module

Volatility indicators measure the rate and magnitude of price fluctuations.

Indicators:
- Bollinger Bands
- ATR (Average True Range)
"""

from indicators.volatility.bollinger import BollingerIndicator
from indicators.volatility.atr import ATRIndicator

# Import modules for backward compatibility (allow "from indicators import atr" style)
from indicators.volatility import bollinger, atr

__all__ = [
    'BollingerIndicator',
    'ATRIndicator',
    'bollinger',
    'atr',
]
