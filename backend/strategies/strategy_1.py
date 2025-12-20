"""
Strategy 1: Balanced Analysis (Default)

Equal weight to all 12 indicators.
This is the current default behavior - good starting point for general analysis.
"""

from typing import Dict, Any, Tuple
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
    
    def validate_buy_signal(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Balanced validation - requires simple condition alignment.
        
        For Strategy 1, we use basic validation:
        - RSI should be in healthy range (30-70)
        - At least 2 momentum indicators should align
        
        Returns:
            (is_valid: bool, reason: str)
        """
        rsi = indicators.get('RSI')
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_signal')
        stochastic = indicators.get('Stochastic')
        
        # RSI should be in healthy range
        if rsi is not None:
            if rsi > 70:
                return False, f"RSI overbought ({rsi:.1f})"
            if rsi < 30:
                return False, f"RSI oversold ({rsi:.1f}) - wait for reversal confirmation"
        
        # Count aligned indicators
        aligned = 0
        if rsi is not None and 40 <= rsi <= 70:
            aligned += 1
        if macd is not None and macd_signal is not None and macd > macd_signal:
            aligned += 1
        if stochastic is not None and 30 <= stochastic <= 70:
            aligned += 1
        
        if aligned < 2:
            return False, f"Only {aligned}/3 indicators aligned (need 2+)"
        
        return True, "Balanced validation passed"
    
    def validate_trend_filter(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Basic trend validation using SMA crossover.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        close = indicators.get('close') or indicators.get('Close')
        sma_20 = indicators.get('SMA_20') or indicators.get('sma_20')
        sma_50 = indicators.get('SMA_50') or indicators.get('sma_50')
        
        if sma_50 is None:
            return True, "SMA_50 not available - trend filter skipped"
        
        if close is not None and close < sma_50:
            return False, f"Price ({close:.2f}) below SMA(50) ({sma_50:.2f})"
        
        if sma_20 is not None and sma_20 < sma_50:
            return False, f"SMA(20) below SMA(50) - bearish alignment"
        
        return True, "Trend filter passed"
    
    def get_cooldown_config(self) -> Dict[str, Any]:
        """Shorter cooldown for balanced strategy."""
        return {
            'use_cooldown': True,
            'cooldown_bars': 2,
            'cooldown_on_stop_loss': True,
            'cooldown_on_time_exit': False,
        }
    
    def get_trade_validation_config(self) -> Dict[str, Any]:
        """Standard trade validation config."""
        return {
            'min_bars_for_valid_trade': 5,
            'skip_incomplete_trades': True,
            'require_trend_filter': True,
            'require_momentum_filter': False,
        }
