"""
Trading Strategies Module

This module provides two systems:

1. Strategy-Based Analysis (NEW):
   - Strategy 1-N: Different indicator weights for different trading styles
   - StrategyManager: Registry for available strategies
   - Used via: StrategyManager.get(strategy_id)

2. Signal Strategies (Existing):
   - Breakout Strategy: Detects price breakouts from consolidation ranges
   - Returns BUY/SELL/NEUTRAL signals with entry, stop-loss, targets

Strategy System:
- Strategies are Python classes (code-defined)
- Database stores only metadata (id, name, description)
- Strategy logic lives in code, not database
"""

from typing import Dict, List, Optional


# =============================================================================
# Strategy-Based Analysis System (NEW)
# =============================================================================

from .base import BaseStrategy


class StrategyManager:
    """
    Registry for all available trading strategies.
    
    Singleton pattern - strategies register themselves on import.
    Provides lookup by ID and listing functionality for API.
    """
    
    _strategies: Dict[int, BaseStrategy] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, strategy: BaseStrategy) -> None:
        """Register a strategy in the manager."""
        cls._strategies[strategy.id] = strategy
    
    @classmethod
    def get(cls, strategy_id: int) -> BaseStrategy:
        """
        Get strategy by ID. Falls back to Strategy 1 if not found.
        """
        cls._ensure_initialized()
        return cls._strategies.get(strategy_id, cls._strategies.get(1))
    
    @classmethod
    def get_default(cls) -> BaseStrategy:
        """Get the default strategy (Strategy 1)."""
        cls._ensure_initialized()
        return cls._strategies.get(1)
    
    @classmethod
    def list_all(cls) -> List[dict]:
        """List all available strategies as dictionaries."""
        cls._ensure_initialized()
        return [s.to_dict() for s in sorted(cls._strategies.values(), key=lambda x: x.id)]
    
    @classmethod
    def list_summary(cls) -> List[dict]:
        """List strategies with minimal info (id, name, description)."""
        cls._ensure_initialized()
        return [
            {'id': s.id, 'name': s.name, 'description': s.description, 'help_url': s.help_url}
            for s in sorted(cls._strategies.values(), key=lambda x: x.id)
        ]
    
    @classmethod
    def get_strategy_ids(cls) -> List[int]:
        """Get list of all registered strategy IDs."""
        cls._ensure_initialized()
        return sorted(cls._strategies.keys())
    
    @classmethod
    def exists(cls, strategy_id: int) -> bool:
        """Check if a strategy ID exists."""
        cls._ensure_initialized()
        return strategy_id in cls._strategies
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure strategies are loaded."""
        if not cls._initialized:
            cls._load_strategies()
            cls._initialized = True
    
    @classmethod
    def _load_strategies(cls) -> None:
        """Import and register all strategy modules."""
        from .strategy_1 import Strategy1
        from .strategy_2 import Strategy2
        from .strategy_3 import Strategy3
        from .strategy_4 import Strategy4
        from .strategy_5 import Strategy5
        
        cls.register(Strategy1())
        cls.register(Strategy2())
        cls.register(Strategy3())
        cls.register(Strategy4())
        cls.register(Strategy5())


# =============================================================================
# Existing Signal Strategies
# =============================================================================

from .breakout_strategy import analyze as breakout_analyze


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Strategy-based analysis
    'StrategyManager',
    'BaseStrategy',
    # Signal strategies
    'breakout_analyze',
]

__version__ = '2.0.0'
