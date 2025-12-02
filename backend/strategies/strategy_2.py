"""
Strategy 2: Trend Following

Emphasizes trend indicators (MACD, ADX, EMA, PSAR).
Best for trending markets with clear directional moves.
"""

from typing import Dict, Any
from .base import BaseStrategy


class Strategy2(BaseStrategy):
    """
    Strategy 2: Trend Following
    
    Heavily weights trend-identifying indicators while reducing
    oscillator influence. Designed to capture sustained directional moves.
    
    Key indicators:
    - MACD (2.5x) - Trend momentum and direction
    - ADX (2.5x) - Trend strength measurement  
    - EMA Crossover (2.0x) - Trend confirmation
    - Parabolic SAR (1.5x) - Trend reversal detection
    
    Best for:
    - Strongly trending markets
    - Breakout trading
    - Swing trading with trend
    """
    
    id = 2
    name = "Strategy 2"
    description = "Trend Following - Emphasizes MACD, ADX, EMA crossovers. Best for trending markets with clear directional moves."
    
    def get_indicator_weights(self) -> Dict[str, float]:
        """Heavy weight on trend indicators, reduced weight on oscillators"""
        return {
            # Trend indicators - HIGH weight
            'macd': 2.5,
            'adx': 2.5,
            'ema': 2.0,
            'psar': 1.5,
            # Momentum indicators - LOW weight (oscillators less useful in trends)
            'rsi': 0.5,
            'stochastic': 0.5,
            'cci': 0.5,
            'williams': 0.5,
            # Volatility indicators - MEDIUM weight
            'bollinger': 0.5,
            'atr': 1.0,  # ATR useful for stop placement in trends
            # Volume indicators - MEDIUM weight (confirmation)
            'obv': 1.0,
            'cmf': 1.0,
        }
    
    def get_category_weights(self) -> Dict[str, float]:
        """Trend category dominates"""
        return {
            'trend': 1.5,
            'momentum': 0.7,
            'volatility': 0.8,
            'volume': 1.0
        }
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """Custom parameters for trend-focused analysis"""
        return {
            'adx': {'threshold': 25},  # Require stronger trend confirmation
            'ema': {'short_period': 9, 'long_period': 21},  # Faster EMAs for trend detection
        }
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """Wider stops and larger targets for trend trading"""
        return {
            'default_stop_loss_pct': 2.5,  # Wider stops to avoid whipsaws
            'default_target_multiplier': 3.0,  # Let winners run in trends
            'max_position_size_pct': 25
        }
