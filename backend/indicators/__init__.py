"""
Technical Indicators Module

Part 3C (MDLRM): Module-Level Rewrite Mode
Organized by category for better maintainability and discovery.

Categories:
- Momentum: RSI, Stochastic, CCI, Williams %R
- Trend: MACD, ADX, EMA, Parabolic SAR, Supertrend
- Volatility: Bollinger Bands, ATR
- Volume: OBV, Chaikin Money Flow

Usage:
    # Using registry (recommended)
    from indicators import IndicatorRegistry
    registry = IndicatorRegistry()
    rsi = registry.get_indicator("RSI")
    
    # Direct import
    from indicators.momentum import RSIIndicator
    
    # Category import
    from indicators.momentum import *
"""

from indicators.base import (
    IndicatorBase,
    MomentumIndicator,
    TrendIndicator,
    VolatilityIndicator,
    VolumeIndicator
)
from indicators.registry import IndicatorRegistry, get_registry

# Import all indicator classes for backward compatibility
from indicators.momentum.rsi import RSIIndicator
from indicators.momentum.stochastic import StochasticIndicator
from indicators.momentum.cci import CCIIndicator
from indicators.momentum.williams import WilliamsIndicator

from indicators.trend.macd import MACDIndicator
from indicators.trend.adx import ADXIndicator
from indicators.trend.ema import EMAIndicator
from indicators.trend.psar import PSARIndicator
from indicators.trend.supertrend import SupertrendIndicator

from indicators.volatility.bollinger import BollingerIndicator
from indicators.volatility.atr import ATRIndicator

from indicators.volume.obv import OBVIndicator
from indicators.volume.cmf import CMFIndicator

# Legacy module imports for backward compatibility
from indicators.momentum import rsi
from indicators.momentum import stochastic
from indicators.momentum import cci
from indicators.momentum import williams
from indicators.trend import macd
from indicators.trend import adx
from indicators.trend import ema
from indicators.trend import psar
from indicators.trend import supertrend
from indicators.volatility import bollinger
from indicators.volatility import atr
from indicators.volume import obv
from indicators.volume import cmf

__all__ = [
    # Base classes
    'IndicatorBase',
    'MomentumIndicator',
    'TrendIndicator',
    'VolatilityIndicator',
    'VolumeIndicator',
    
    # Registry
    'IndicatorRegistry',
    'get_registry',
    
    # Momentum indicators
    'RSIIndicator',
    'StochasticIndicator',
    'CCIIndicator',
    'WilliamsIndicator',
    
    # Trend indicators
    'MACDIndicator',
    'ADXIndicator',
    'EMAIndicator',
    'PSARIndicator',
    'SupertrendIndicator',
    
    # Volatility indicators
    'BollingerIndicator',
    'ATRIndicator',
    
    # Volume indicators
    'OBVIndicator',
    'CMFIndicator',
    
    # Legacy module names
    'rsi',
    'macd',
    'adx',
    'psar',
    'ema',
    'stochastic',
    'cci',
    'williams',
    'atr',
    'bollinger',
    'obv',
    'cmf',
    'supertrend',
]


