"""
Strategy 3: Mean Reversion

Emphasizes oscillators and mean-reversion indicators (RSI, Bollinger, Stochastic).
Best for range-bound/sideways markets where prices oscillate.
"""

from typing import Dict, Any
from .base import BaseStrategy


class Strategy3(BaseStrategy):
    """
    Strategy 3: Mean Reversion
    
    Focuses on oscillators that identify overbought/oversold conditions.
    Designed to catch price reversals back toward the mean.
    
    Key indicators:
    - RSI (2.5x) - Primary overbought/oversold detection
    - Bollinger Bands (2.5x) - Price deviation from mean
    - Stochastic (2.0x) - Momentum exhaustion
    - CCI/Williams (1.5x) - Secondary oscillator confirmation
    
    Best for:
    - Range-bound/sideways markets
    - Stocks with clear support/resistance
    - Counter-trend trading
    """
    
    id = 3
    name = "Strategy 3"
    description = "Mean Reversion - Emphasizes RSI, Bollinger Bands, Stochastic. Best for range-bound markets where prices oscillate."
    
    def get_indicator_weights(self) -> Dict[str, float]:
        """Heavy weight on oscillators, reduced weight on trend indicators"""
        return {
            # Trend indicators - LOW weight (trends less relevant for mean reversion)
            'macd': 0.5,
            'adx': 0.5,  # Low ADX actually confirms range-bound market
            'ema': 0.5,
            'psar': 0.5,
            # Momentum indicators - HIGH weight (core of mean reversion)
            'rsi': 2.5,
            'stochastic': 2.0,
            'cci': 1.5,
            'williams': 1.5,
            # Volatility indicators - HIGH weight (Bollinger key for mean reversion)
            'bollinger': 2.5,
            'atr': 1.0,
            # Volume indicators - MEDIUM weight
            'obv': 1.0,
            'cmf': 1.0,
        }
    
    def get_category_weights(self) -> Dict[str, float]:
        """Momentum and volatility categories dominate"""
        return {
            'trend': 0.6,
            'momentum': 1.5,
            'volatility': 1.3,
            'volume': 1.0
        }
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """Standard oscillator parameters"""
        return {
            'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
            'stochastic': {'k_period': 14, 'overbought': 80, 'oversold': 20},
        }
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """Tighter stops and smaller targets for range trading"""
        return {
            'default_stop_loss_pct': 1.5,  # Tighter stops in ranges
            'default_target_multiplier': 1.5,  # Smaller, more frequent targets
            'max_position_size_pct': 15  # Smaller positions due to counter-trend nature
        }
