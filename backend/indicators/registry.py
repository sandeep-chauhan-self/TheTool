"""
Indicator Registry - Centralized Indicator Management

Part 3C (MDLRM): Module-Level Rewrite Mode
Provides:
- Thread-safe singleton registry for all indicators
- Category-based filtering (momentum, trend, volatility, volume)
- Lazy instantiation and caching
- Discovery and metadata access

Usage:
    from indicators.registry import IndicatorRegistry
    
    registry = IndicatorRegistry()
    
    # Get single indicator
    rsi = registry.get_indicator("RSI")
    
    # Get by category
    momentum_indicators = registry.get_by_category("momentum")
    
    # Get all names
    all_names = registry.get_all_names()
"""

import threading
from typing import Dict, List, Optional
from indicators.base import IndicatorBase
import logging

logger = logging.getLogger(__name__)


class IndicatorRegistry:
    """
    Thread-safe singleton registry for managing all technical indicators.
    
    Features:
    - Automatic indicator discovery from categorized modules
    - Category-based filtering
    - Lazy instantiation with caching
    - Thread-safe singleton pattern
    - Metadata access (names, categories)
    
    Part 3C Design:
    - Eliminates tight coupling between indicators and consumers
    - Central point for indicator management
    - Enables dynamic indicator loading
    - Supports testing with mock indicators
    """
    
    _instance: Optional['IndicatorRegistry'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'IndicatorRegistry':
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize registry (only once due to singleton)"""
        if self._initialized:
            return
        
        self._indicators: Dict[str, IndicatorBase] = {}
        self._category_map: Dict[str, List[str]] = {
            'momentum': [],
            'trend': [],
            'volatility': [],
            'volume': []
        }
        
        try:
            self._register_all_indicators()
            self._initialized = True
            logger.info(f"IndicatorRegistry initialized with {len(self._indicators)} indicators")
        except Exception as e:
            logger.error(f"Failed to initialize IndicatorRegistry: {e}")
            raise
    
    def _register_all_indicators(self) -> None:
        """
        Register all available indicators from categorized modules.
        
        Uses dynamic imports to avoid circular dependencies and
        support lazy loading.
        """
        # Import indicator classes by category
        indicator_classes = self._discover_indicators()
        
        # Instantiate and register each indicator
        for indicator_class in indicator_classes:
            try:
                indicator = indicator_class()
                self._indicators[indicator.name] = indicator
                
                # Add to category map
                category = indicator.category
                if category in self._category_map:
                    self._category_map[category].append(indicator.name)
                
            except Exception as e:
                logger.error(f"Failed to register {indicator_class.__name__}: {e}")
    
    def _discover_indicators(self) -> List[type]:
        """
        Discover all indicator classes from categorized modules.
        
        Returns:
            List of indicator class types
        """
        indicators = []
        
        # Momentum indicators
        try:
            from indicators.momentum.rsi import RSIIndicator
            from indicators.momentum.stochastic import StochasticIndicator
            from indicators.momentum.cci import CCIIndicator
            from indicators.momentum.williams import WilliamsIndicator
            indicators.extend([RSIIndicator, StochasticIndicator, CCIIndicator, WilliamsIndicator])
        except ImportError as e:
            logger.warning(f"Could not import momentum indicators: {e}")
        
        # Trend indicators
        try:
            from indicators.trend.macd import MACDIndicator
            from indicators.trend.adx import ADXIndicator
            from indicators.trend.ema import EMAIndicator
            from indicators.trend.psar import PSARIndicator
            from indicators.trend.supertrend import SupertrendIndicator
            indicators.extend([MACDIndicator, ADXIndicator, EMAIndicator, PSARIndicator, SupertrendIndicator])
        except ImportError as e:
            logger.warning(f"Could not import trend indicators: {e}")
        
        # Volatility indicators
        try:
            from indicators.volatility.bollinger import BollingerIndicator
            from indicators.volatility.atr import ATRIndicator
            indicators.extend([BollingerIndicator, ATRIndicator])
        except ImportError as e:
            logger.warning(f"Could not import volatility indicators: {e}")
        
        # Volume indicators
        try:
            from indicators.volume.obv import OBVIndicator
            from indicators.volume.cmf import CMFIndicator
            indicators.extend([OBVIndicator, CMFIndicator])
        except ImportError as e:
            logger.warning(f"Could not import volume indicators: {e}")
        
        return indicators
    
    def get_indicator(self, name: str) -> IndicatorBase:
        """
        Get indicator instance by name.
        
        Args:
            name: Indicator name (e.g., "RSI", "MACD")
        
        Returns:
            IndicatorBase: Indicator instance
        
        Raises:
            KeyError: If indicator name not found
        """
        if name not in self._indicators:
            available = ', '.join(self._indicators.keys())
            raise KeyError(
                f"Unknown indicator: '{name}'. "
                f"Available indicators: {available}"
            )
        return self._indicators[name]
    
    def get_indicators(self, names: Optional[List[str]] = None) -> List[IndicatorBase]:
        """
        Get multiple indicator instances.
        
        Args:
            names: List of indicator names (None = all indicators)
        
        Returns:
            List[IndicatorBase]: List of indicator instances
        """
        if names is None:
            return list(self._indicators.values())
        
        return [self.get_indicator(name) for name in names]
    
    def get_by_category(self, category: str) -> List[IndicatorBase]:
        """
        Get all indicators in a specific category.
        
        Args:
            category: Category name ('momentum', 'trend', 'volatility', 'volume')
        
        Returns:
            List[IndicatorBase]: List of indicators in category
        
        Raises:
            ValueError: If category invalid
        """
        if category not in self._category_map:
            valid = ', '.join(self._category_map.keys())
            raise ValueError(
                f"Invalid category: '{category}'. "
                f"Valid categories: {valid}"
            )
        
        indicator_names = self._category_map[category]
        return [self._indicators[name] for name in indicator_names]
    
    def get_all_names(self) -> List[str]:
        """
        Get names of all registered indicators.
        
        Returns:
            List[str]: Sorted list of indicator names
        """
        return sorted(self._indicators.keys())
    
    def get_categories(self) -> List[str]:
        """
        Get all available categories.
        
        Returns:
            List[str]: List of category names
        """
        return list(self._category_map.keys())
    
    def get_category_info(self) -> Dict[str, int]:
        """
        Get indicator count per category.
        
        Returns:
            Dict[str, int]: Category name -> count mapping
        """
        return {
            category: len(indicators)
            for category, indicators in self._category_map.items()
        }
    
    def has_indicator(self, name: str) -> bool:
        """
        Check if indicator is registered.
        
        Args:
            name: Indicator name
        
        Returns:
            bool: True if indicator exists
        """
        return name in self._indicators
    
    def __len__(self) -> int:
        """Return total number of registered indicators"""
        return len(self._indicators)
    
    def __repr__(self) -> str:
        """String representation showing registry stats"""
        return (
            f"IndicatorRegistry("
            f"total={len(self._indicators)}, "
            f"categories={len(self._category_map)})"
        )


# Convenience function for quick access
def get_registry() -> IndicatorRegistry:
    """
    Get the global indicator registry instance.
    
    Returns:
        IndicatorRegistry: Singleton registry instance
    """
    return IndicatorRegistry()
