"""
Strategy 5: Weekly 4% Target (Aggressive Swing Trading)

Optimized for 4% minimum weekly gains with 3% stop loss (1.33:1 R:R).
High momentum focus for quick price moves.
"""

from typing import Dict, Any
from .base import BaseStrategy


class Strategy5(BaseStrategy):
    """
    Strategy 5: Weekly 4% Target
    
    Aggressive swing trading strategy designed to hit 4% profit target within one week.
    
    Key characteristics:
    - Stop Loss: 3% (e.g., ₹97 if buy at ₹100)
    - Target: 4% (e.g., ₹104 if buy at ₹100)
    - Risk-Reward Ratio: 1.33:1
    - High momentum indicator focus
    - Fast-period technical indicators
    
    Best for:
    - Experienced traders
    - Shorter time frames (1-7 days)
    - High-volatility stocks
    - Quick profit-taking strategies
    
    Example Trade:
    - Buy at ₹100 with momentum confirmation
    - Stop Loss: ₹97 (3% risk = ₹3)
    - Target: ₹104 (4% gain = ₹4)
    - Risk-Reward: 1.33:1 (0.75 stop to reach target)
    """
    
    id = 5
    name = "Strategy 5"
    description = "Weekly 4% Target - Aggressive swing trading for 4% weekly gains. 3% stop, 4% target (1.33:1 R:R)."
    
    def get_indicator_weights(self) -> Dict[str, float]:
        """
        Prioritize momentum and fast-moving indicators for quick reversals.
        De-emphasize slower trend confirmation.
        """
        return {
            # Trend indicators (lower weight for faster signals)
            'macd': 1.2,          # MACD crossovers for momentum
            'adx': 0.7,           # ADX (lower priority - slow trend)
            'ema': 0.8,           # EMA (lower priority)
            'psar': 1.0,          # SAR for quick exits
            
            # Momentum indicators (HIGHEST PRIORITY for quick moves)
            'rsi': 1.6,           # Oversold/overbought (fast reversal signals)
            'stochastic': 1.6,    # Stochastic (fast oscillator)
            'cci': 1.4,           # CCI (commodity channel for swing trading)
            'williams': 1.3,      # Williams %R (momentum extremes)
            
            # Volatility indicators (for risk management)
            'bollinger': 1.2,     # Bollinger Bands (breakout confirmation)
            'atr': 1.0,           # ATR (position sizing)
            
            # Volume indicators (confirmation only)
            'obv': 1.0,           # OBV (volume trend)
            'cmf': 1.0,           # CMF (money flow confirmation)
        }
    
    def get_category_weights(self) -> Dict[str, float]:
        """
        Momentum category dominates for quick price moves.
        Volatility important for risk management.
        Trend and volume are secondary.
        """
        return {
            'momentum': 1.6,      # Highest priority - quick price moves
            'volatility': 1.2,    # Risk management
            'trend': 0.8,         # Lower priority - we want faster signals
            'volume': 0.9         # Confirmation only
        }
    
    def get_indicator_params(self) -> Dict[str, Dict[str, Any]]:
        """
        Use faster periods for quicker signal generation.
        Override default periods to detect quick moves earlier.
        """
        return {
            'rsi_period': 10,              # Fast RSI (default 14)
            'macd_fast': 8,                # Fast MACD (default 12)
            'macd_slow': 17,               # Slow MACD (default 26)
            'macd_signal': 9,              # Signal (default 9)
            'stochastic_period': 10,       # Fast Stochastic (default 14)
            'ema_fast': 8,                 # Fast EMA (default 12)
            'ema_slow': 17,                # Slow EMA (default 26)
            'bollinger_period': 15,        # Fast Bollinger (default 20)
        }
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """
        Fixed risk profile for 4% weekly target:
        - Stop Loss: 3% (e.g., ₹97 if buy at ₹100)
        - Target: 4% (e.g., ₹104 if buy at ₹100)
        - 1.33:1 risk-reward ratio
        - Larger position sizing for short-term trades
        """
        return {
            'default_stop_loss_pct': 3.0,          # 3% stop (e.g., 100 -> 97)
            'default_target_multiplier': 1.33,    # 1.33  3% = 4% target (100 -> 104)
            'max_position_size_pct': 30,           # Can take bigger positions for short term
            'min_reward_pct': 4.0,                 # Enforce minimum 4% reward
        }
