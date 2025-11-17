"""
Trading Strategies Module

This module contains various trading strategies that analyze stock data
and provide actionable trading signals with entry, stop-loss, and target prices.

Each strategy:
- Analyzes OHLCV data and indicator results
- Returns BUY/SELL/NEUTRAL signal with confidence
- Provides specific entry, stop-loss, and target prices
- Works alongside indicator signals (parallel voting system)

Available Strategies:
- Breakout Strategy: Detects price breakouts from consolidation ranges
"""

# Import all strategies here as they are created
from .breakout_strategy import analyze as breakout_analyze

__all__ = [
    'breakout_analyze',
]

__version__ = '1.0.0'
