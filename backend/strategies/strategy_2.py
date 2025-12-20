"""
Strategy 2: Trend Following

Emphasizes trend indicators (MACD, ADX, EMA, PSAR).
Best for trending markets with clear directional moves.
"""

from typing import Dict, Any, Tuple
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
    
    def validate_buy_signal(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Trend following validation - requires strong trend confirmation.
        
        Key requirements:
        - ADX > 25 (strong trend)
        - MACD bullish (above signal line)
        - RSI in healthy range (40-80)
        
        Returns:
            (is_valid: bool, reason: str)
        """
        rsi = indicators.get('RSI')
        adx = indicators.get('ADX')
        macd = indicators.get('MACD')
        macd_signal = indicators.get('MACD_signal')
        
        # ADX must show strong trend
        if adx is not None:
            if adx < 25:
                return False, f"ADX too weak ({adx:.1f}) - need > 25 for trend confirmation"
        
        # MACD must be bullish
        if macd is not None and macd_signal is not None:
            if macd <= macd_signal:
                return False, f"MACD not bullish ({macd:.2f} ≤ {macd_signal:.2f})"
        
        # RSI should support trend (higher range acceptable)
        if rsi is not None:
            if rsi > 80:
                return False, f"RSI extremely overbought ({rsi:.1f})"
            if rsi < 40:
                return False, f"RSI too weak for trend ({rsi:.1f}) - need > 40"
        
        return True, "Trend validation passed - strong trend confirmed"
    
    def validate_trend_filter(self, indicators: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Strict trend validation - price must be in clear uptrend.
        
        Returns:
            (is_valid: bool, reason: str)
        """
        close = indicators.get('close') or indicators.get('Close')
        sma_20 = indicators.get('SMA_20') or indicators.get('sma_20')
        sma_50 = indicators.get('SMA_50') or indicators.get('sma_50')
        adx = indicators.get('ADX')
        
        if sma_50 is None:
            return True, "SMA_50 not available - trend filter skipped"
        
        # Price must be above SMA 50
        if close is not None and close < sma_50:
            return False, f"Price ({close:.2f}) below SMA(50) ({sma_50:.2f}) - no uptrend"
        
        # SMA 20 must be above SMA 50
        if sma_20 is not None and sma_20 < sma_50:
            return False, f"SMA(20) below SMA(50) - bearish crossover"
        
        # ADX must confirm trend
        if adx is not None and adx < 20:
            return False, f"ADX ({adx:.1f}) too low - market not trending"
        
        return True, "Strong uptrend confirmed"
    
    def get_cooldown_config(self) -> Dict[str, Any]:
        """Moderate cooldown for trend strategy."""
        return {
            'use_cooldown': True,
            'cooldown_bars': 3,
            'cooldown_on_stop_loss': True,
            'cooldown_on_time_exit': False,
        }
    
    def get_trade_validation_config(self) -> Dict[str, Any]:
        """Trend validation config - strict on trend filter."""
        return {
            'min_bars_for_valid_trade': 5,
            'skip_incomplete_trades': True,
            'require_trend_filter': True,  # Essential for trend following
            'require_momentum_filter': False,
        }
