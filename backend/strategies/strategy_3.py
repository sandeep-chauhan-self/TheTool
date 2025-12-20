"""
Strategy 3: Mean Reversion

Emphasizes oscillators and mean-reversion indicators (RSI, Bollinger, Stochastic).
Best for range-bound/sideways markets where prices oscillate.
"""

from typing import Dict, Any, Tuple
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
    
    def validate_buy_signal(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Mean reversion validation - looks for oversold conditions.
        
        Key requirements:
        - RSI oversold (< 40) indicates buying opportunity
        - Stochastic should also be low (< 30)
        - ADX should be LOW (range-bound market)
        
        Returns:
            (is_valid: bool, reason: str)
        """
        rsi = indicators.get('RSI')
        stochastic = indicators.get('Stochastic')
        adx = indicators.get('ADX')
        williams = indicators.get('Williams %R')
        
        # For mean reversion, we WANT low RSI (oversold)
        if rsi is not None:
            if rsi > 50:
                return False, f"RSI too high ({rsi:.1f}) - wait for oversold (<40)"
        
        # Count oversold signals
        oversold_count = 0
        if rsi is not None and rsi < 40:
            oversold_count += 1
        if stochastic is not None and stochastic < 30:
            oversold_count += 1
        if williams is not None and williams < -80:  # Williams is -100 to 0
            oversold_count += 1
        
        if oversold_count < 1:
            return False, f"No oversold signals ({oversold_count}/3) - mean reversion needs oversold"
        
        # ADX should be LOW for range-bound market
        if adx is not None and adx > 25:
            return False, f"ADX too high ({adx:.1f}) - market trending, not range-bound"
        
        return True, f"Mean reversion entry: {oversold_count}/3 oversold signals"
    
    def validate_trend_filter(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        For mean reversion, we DON'T want strong trends.
        Low ADX and price near mean is ideal.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        adx = indicators.get('ADX')
        
        # We actually WANT low ADX for mean reversion
        if adx is not None and adx > 30:
            return False, f"ADX ({adx:.1f}) too high - market trending, not suitable for mean reversion"
        
        # For mean reversion, trend filter is inverse - we pass if NOT trending
        return True, "Range-bound market confirmed"
    
    def get_cooldown_config(self) -> Dict[str, Any]:
        """Shorter cooldown - mean reversion re-enters faster."""
        return {
            'use_cooldown': True,
            'cooldown_bars': 2,
            'cooldown_on_stop_loss': True,
            'cooldown_on_time_exit': False,
        }
    
    def get_trade_validation_config(self) -> Dict[str, Any]:
        """Mean reversion config - no trend filter."""
        return {
            'min_bars_for_valid_trade': 3,  # Shorter trades
            'skip_incomplete_trades': True,
            'require_trend_filter': False,  # Don't use trend filter for mean reversion
            'require_momentum_filter': False,
        }
