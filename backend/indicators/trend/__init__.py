"""
Trend Indicators Module

Trend indicators identify the direction and strength of market trends.

Indicators:
- MACD (Moving Average Convergence Divergence)
- ADX (Average Directional Index)
- EMA (Exponential Moving Average)
- Parabolic SAR (Stop and Reverse)
- Supertrend
"""

from indicators.trend.macd import MACDIndicator
from indicators.trend.adx import ADXIndicator
from indicators.trend.ema import EMAIndicator
from indicators.trend.psar import PSARIndicator
from indicators.trend.supertrend import SupertrendIndicator

__all__ = [
    'MACDIndicator',
    'ADXIndicator',
    'EMAIndicator',
    'PSARIndicator',
    'SupertrendIndicator',
]
