"""
Strategy 4: Momentum Breakout

Volume-confirmed momentum signals.
Best for catching breakouts with strong volume confirmation.
"""

from typing import Dict, Any
from .base import BaseStrategy


class Strategy4(BaseStrategy):
    """
    Strategy 4: Momentum Breakout
    
    Combines momentum indicators with volume confirmation.
    Designed to catch breakouts that have institutional backing.
    
    Key indicators:
    - OBV (2.5x) - Volume accumulation/distribution
    - CMF (2.5x) - Money flow direction
    - RSI (2.0x) - Momentum confirmation
    - ATR (2.0x) - Volatility expansion on breakout
    
    Best for:
    - Breakout trading
    - High-volume momentum plays
    - Catching institutional moves
    """
    
    id = 4
    name = "Strategy 4"
    description = "Momentum Breakout - Volume-confirmed momentum signals. Best for catching breakouts with strong volume confirmation."
    
    def get_indicator_weights(self) -> Dict[str, float]:
        """Heavy weight on volume and momentum, medium on trend"""
        return {
            # Trend indicators - MEDIUM weight (trend confirmation)
            'macd': 1.5,
            'adx': 1.5,  # ADX confirms trend strength on breakout
            'ema': 1.0,
            'psar': 1.0,
            # Momentum indicators - HIGH weight
            'rsi': 2.0,
            'stochastic': 1.5,
            'cci': 1.5,
            'williams': 1.0,
            # Volatility indicators - HIGH weight (ATR expansion confirms breakout)
            'bollinger': 1.5,
            'atr': 2.0,
            # Volume indicators - HIGHEST weight (core of strategy)
            'obv': 2.5,
            'cmf': 2.5,
        }
    
    def get_category_weights(self) -> Dict[str, float]:
        """Volume category dominates, momentum second"""
        return {
            'trend': 1.0,
            'momentum': 1.3,
            'volatility': 1.2,
            'volume': 1.5
        }
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """Parameters tuned for breakout detection"""
        return {
            'adx': {'threshold': 20},  # Lower threshold to catch early breakouts
        }
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """Wider stops for volatile breakouts"""
        return {
            'default_stop_loss_pct': 3.0,  # Wider stops for breakout volatility
            'default_target_multiplier': 2.5,  # Good targets on confirmed breakouts
            'max_position_size_pct': 20
        }
