"""
Strategy 1: Balanced Analysis (Default)

Equal weight to all 12 indicators.
This is the current default behavior - good starting point for general analysis.
"""

from typing import Dict, Any
from .base import BaseStrategy


class Strategy1(BaseStrategy):
    """
    Strategy 1: Balanced Analysis
    
    Equal weight to all indicators across all categories.
    Provides comprehensive market view without bias toward any trading style.
    
    Best for:
    - General market scanning
    - Beginners learning technical analysis
    - When market conditions are unclear
    """
    
    id = 1
    name = "Strategy 1"
    description = "Balanced Analysis - Equal weight to all 12 indicators. Good starting point for general market analysis."
    
    def get_indicator_weights(self) -> Dict[str, float]:
        """All indicators have equal weight of 1.0"""
        return {
            # Trend indicators
            'macd': 1.0,
            'adx': 1.0,
            'ema': 1.0,
            'psar': 1.0,
            # Momentum indicators
            'rsi': 1.0,
            'stochastic': 1.0,
            'cci': 1.0,
            'williams': 1.0,
            # Volatility indicators
            'bollinger': 1.0,
            'atr': 1.0,
            # Volume indicators
            'obv': 1.0,
            'cmf': 1.0,
        }
    
    def get_category_weights(self) -> Dict[str, float]:
        """All categories have equal weight"""
        return {
            'trend': 1.0,
            'momentum': 1.0,
            'volatility': 1.0,
            'volume': 1.0
        }
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """Use default parameters for all indicators"""
        return {}
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """Standard risk profile"""
        return {
            'default_stop_loss_pct': 2.0,
            'default_target_multiplier': 2.0,
            'max_position_size_pct': 20
        }
