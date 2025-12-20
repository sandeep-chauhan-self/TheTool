"""
Strategy 4: Momentum Breakout

Volume-confirmed momentum signals.
Best for catching breakouts with strong volume confirmation.
"""

from typing import Dict, Any, Tuple
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
    
    def validate_buy_signal(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Breakout validation - requires volume confirmation.
        
        Key requirements:
        - Volume surge (> 1.5x average)
        - RSI showing strength (> 50)
        - MACD bullish preferred
        
        Returns:
            (is_valid: bool, reason: str)
        """
        rsi = indicators.get('RSI')
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_signal')
        volume_ratio = indicators.get('volume_ratio', 1.0)
        cmf = indicators.get('CMF')
        obv = indicators.get('OBV')
        obv_prev = indicators.get('OBV_prev')
        
        # Volume surge is CRITICAL for breakout
        if volume_ratio < 1.3:
            return False, f"Volume too low ({volume_ratio:.2f}x) - breakout needs 1.3x+ volume"
        
        # RSI must show strength (not exhausted)
        if rsi is not None:
            if rsi < 50:
                return False, f"RSI too weak ({rsi:.1f}) - breakout needs momentum"
            if rsi > 85:
                return False, f"RSI extremely overbought ({rsi:.1f}) - breakout exhausted"
        
        # MACD bullish preferred
        macd_bullish = macd is not None and macd_signal is not None and macd > macd_signal
        
        # CMF positive preferred (money flowing in)
        cmf_positive = cmf is not None and cmf > 0
        
        # OBV rising preferred
        obv_rising = obv is not None and obv_prev is not None and obv > obv_prev
        
        # Count volume confirmations
        volume_confirms = sum([macd_bullish, cmf_positive, obv_rising])
        
        if volume_confirms < 1:
            return False, f"No volume confirmation ({volume_confirms}/3) - need MACD/CMF/OBV support"
        
        return True, f"Breakout confirmed: {volume_ratio:.2f}x volume, {volume_confirms}/3 confirmations"
    
    def validate_trend_filter(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Breakout needs directional confirmation, but not as strict as trend following.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        close = indicators.get('close') or indicators.get('Close')
        sma_20 = indicators.get('SMA_20') or indicators.get('sma_20')
        sma_50 = indicators.get('SMA_50') or indicators.get('sma_50')
        
        if sma_50 is None:
            return True, "SMA_50 not available - trend filter skipped"
        
        # Price should be above SMA 20 (immediate trend)
        if close is not None and sma_20 is not None and close < sma_20:
            return False, f"Price ({close:.2f}) below SMA(20) - no immediate breakout"
        
        # SMA 50 is less critical for breakouts - we're looking for new trends
        
        return True, "Breakout direction confirmed"
    
    def get_cooldown_config(self) -> Dict[str, Any]:
        """Shorter cooldown - breakouts can happen in clusters."""
        return {
            'use_cooldown': True,
            'cooldown_bars': 2,
            'cooldown_on_stop_loss': True,
            'cooldown_on_time_exit': False,
        }
    
    def get_trade_validation_config(self) -> Dict[str, Any]:
        """Breakout config - volume is key."""
        return {
            'min_bars_for_valid_trade': 5,
            'skip_incomplete_trades': True,
            'require_trend_filter': True,
            'require_momentum_filter': False,
            'require_volume_surge': True,  # Critical for breakout strategy
        }
