"""
Part 3C Test Suite - Indicator Registry

Tests the new IndicatorRegistry singleton for:
- Thread-safe singleton pattern
- Category-based filtering
- Indicator discovery
- Error handling
"""

import pytest
import threading
from indicators.registry import IndicatorRegistry, get_registry
from indicators.base import IndicatorBase


class TestIndicatorRegistry:
    """Test IndicatorRegistry functionality"""
    
    def test_singleton_pattern(self):
        """Test that only one registry instance exists"""
        registry1 = IndicatorRegistry()
        registry2 = IndicatorRegistry()
        registry3 = get_registry()
        
        assert registry1 is registry2
        assert registry2 is registry3
        assert id(registry1) == id(registry2) == id(registry3)
    
    def test_thread_safe_singleton(self):
        """Test singleton is thread-safe"""
        instances = []
        
        def get_instance():
            instances.append(IndicatorRegistry())
        
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All instances should be the same object
        first_id = id(instances[0])
        assert all(id(inst) == first_id for inst in instances)
    
    def test_registry_initialization(self):
        """Test registry initializes with all indicators"""
        registry = IndicatorRegistry()
        
        # Should have 13 indicators
        assert len(registry) == 13
        
        # Should have 4 categories
        assert len(registry.get_categories()) == 4
    
    def test_get_indicator_by_name(self):
        """Test getting indicator by name"""
        registry = IndicatorRegistry()
        
        # Get RSI indicator
        rsi = registry.get_indicator("RSI")
        assert rsi is not None
        assert rsi.name == "RSI"
        assert isinstance(rsi, IndicatorBase)
        
        # Get MACD indicator
        macd = registry.get_indicator("MACD")
        assert macd is not None
        assert macd.name == "MACD"
    
    def test_get_indicator_unknown_name(self):
        """Test error handling for unknown indicator"""
        registry = IndicatorRegistry()
        
        with pytest.raises(KeyError, match="Unknown indicator"):
            registry.get_indicator("NonExistent")
    
    def test_get_all_indicators(self):
        """Test getting all indicators"""
        registry = IndicatorRegistry()
        
        all_indicators = registry.get_indicators()
        assert len(all_indicators) == 13
        assert all(isinstance(ind, IndicatorBase) for ind in all_indicators)
    
    def test_get_specific_indicators(self):
        """Test getting specific list of indicators"""
        registry = IndicatorRegistry()
        
        indicators = registry.get_indicators(["RSI", "MACD", "Bollinger Bands"])
        assert len(indicators) == 3
        assert indicators[0].name == "RSI"
        assert indicators[1].name == "MACD"
        assert indicators[2].name == "Bollinger Bands"
    
    def test_get_by_category_momentum(self):
        """Test getting momentum indicators"""
        registry = IndicatorRegistry()
        
        momentum = registry.get_by_category("momentum")
        assert len(momentum) == 4  # RSI, Stochastic, CCI, Williams %R
        
        momentum_names = [ind.name for ind in momentum]
        assert "RSI" in momentum_names
        assert "Stochastic" in momentum_names
        assert "CCI" in momentum_names
        assert "Williams %R" in momentum_names
    
    def test_get_by_category_trend(self):
        """Test getting trend indicators"""
        registry = IndicatorRegistry()
        
        trend = registry.get_by_category("trend")
        assert len(trend) == 5  # MACD, ADX, EMA, PSAR, Supertrend
        
        trend_names = [ind.name for ind in trend]
        assert "MACD" in trend_names
        assert "ADX" in trend_names
    
    def test_get_by_category_volatility(self):
        """Test getting volatility indicators"""
        registry = IndicatorRegistry()
        
        volatility = registry.get_by_category("volatility")
        assert len(volatility) == 2  # Bollinger, ATR
        
        volatility_names = [ind.name for ind in volatility]
        assert "Bollinger Bands" in volatility_names
        assert "ATR" in volatility_names
    
    def test_get_by_category_volume(self):
        """Test getting volume indicators"""
        registry = IndicatorRegistry()
        
        volume = registry.get_by_category("volume")
        assert len(volume) == 2  # OBV, CMF
        
        volume_names = [ind.name for ind in volume]
        assert "OBV" in volume_names
        assert "Chaikin Money Flow" in volume_names
    
    def test_get_by_category_invalid(self):
        """Test error handling for invalid category"""
        registry = IndicatorRegistry()
        
        with pytest.raises(ValueError, match="Invalid category"):
            registry.get_by_category("invalid")
    
    def test_get_all_names(self):
        """Test getting all indicator names"""
        registry = IndicatorRegistry()
        
        names = registry.get_all_names()
        assert len(names) == 13
        assert "RSI" in names
        assert "MACD" in names
        assert "Bollinger Bands" in names
        
        # Should be sorted
        assert names == sorted(names)
    
    def test_get_categories(self):
        """Test getting all categories"""
        registry = IndicatorRegistry()
        
        categories = registry.get_categories()
        assert len(categories) == 4
        assert "momentum" in categories
        assert "trend" in categories
        assert "volatility" in categories
        assert "volume" in categories
    
    def test_get_category_info(self):
        """Test getting category statistics"""
        registry = IndicatorRegistry()
        
        info = registry.get_category_info()
        assert info["momentum"] == 4
        assert info["trend"] == 5
        assert info["volatility"] == 2
        assert info["volume"] == 2
    
    def test_has_indicator(self):
        """Test checking indicator existence"""
        registry = IndicatorRegistry()
        
        assert registry.has_indicator("RSI") is True
        assert registry.has_indicator("MACD") is True
        assert registry.has_indicator("NonExistent") is False
    
    def test_registry_repr(self):
        """Test string representation"""
        registry = IndicatorRegistry()
        
        repr_str = repr(registry)
        assert "IndicatorRegistry" in repr_str
        assert "total=13" in repr_str
        assert "categories=4" in repr_str
    
    def test_indicator_reuse(self):
        """Test that getting same indicator returns same instance"""
        registry = IndicatorRegistry()
        
        rsi1 = registry.get_indicator("RSI")
        rsi2 = registry.get_indicator("RSI")
        
        # Should be same object (cached)
        assert rsi1 is rsi2
        assert id(rsi1) == id(rsi2)


class TestBackwardCompatibility:
    """Test that Part 3C maintains backward compatibility"""
    
    def test_direct_imports_still_work(self):
        """Test that old import style still works"""
        from indicators.momentum.rsi import RSIIndicator
        from indicators.trend.macd import MACDIndicator
        
        rsi = RSIIndicator()
        macd = MACDIndicator()
        
        assert rsi.name == "RSI"
        assert macd.name == "MACD"
    
    def test_category_imports_work(self):
        """Test importing from category modules"""
        from indicators.momentum import RSIIndicator, StochasticIndicator
        from indicators.trend import MACDIndicator, ADXIndicator
        
        assert RSIIndicator is not None
        assert MACDIndicator is not None
    
    def test_main_init_imports(self):
        """Test imports from main indicators module"""
        from indicators import RSIIndicator, MACDIndicator, IndicatorRegistry
        
        assert RSIIndicator is not None
        assert MACDIndicator is not None
        assert IndicatorRegistry is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
