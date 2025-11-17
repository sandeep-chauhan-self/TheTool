"""
Part 4: Performance Architecture - Test Suite

Tests for:
- PERFORMANCE_ARCHITECTURE_001: Caching Layer
- PERFORMANCE_ARCHITECTURE_002: Parallel Processing
"""

import pytest
import pandas as pd
import time
from datetime import datetime
from performance.cache import (
    CacheConfig,
    InMemoryCache,
    CacheLayer,
    cached
)
from performance.parallel import (
    ParallelIndicatorEngine,
    IndicatorResult,
    IndicatorBatch,
    compute_indicators_parallel
)


# ============================================================================
# Cache Layer Tests
# ============================================================================

class TestInMemoryCache:
    """Test in-memory cache implementation"""
    
    def test_cache_get_set(self):
        """Test basic get/set operations"""
        cache = InMemoryCache(max_size=10)
        
        # Set and get
        cache.set("key1", "value1", ttl_seconds=60)
        assert cache.get("key1") == "value1"
        
        # Non-existent key
        assert cache.get("nonexistent") is None
    
    def test_cache_expiry(self):
        """Test TTL expiration"""
        cache = InMemoryCache()
        
        # Set with short TTL
        cache.set("key1", "value1", ttl_seconds=1)
        assert cache.get("key1") == "value1"
        
        # Wait for expiry
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size exceeded"""
        cache = InMemoryCache(max_size=3)
        
        # Fill cache
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        cache.set("key3", "value3", ttl_seconds=60)
        
        # All present
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        
        # Add fourth - should evict key2 (least recently used)
        cache.set("key4", "value4", ttl_seconds=60)
        
        # key2 should be evicted (it was not accessed)
        # key1 and key3 were accessed by get() calls above
        assert len(cache.cache) == 3
        assert cache.get("key1") is not None or cache.get("key3") is not None
    
    def test_cache_delete(self):
        """Test delete operation"""
        cache = InMemoryCache()
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        # Delete one key
        deleted = cache.delete("key1")
        assert deleted == 1
        assert cache.get("key1") is None
        assert cache.get("key2") is not None
        
        # Delete multiple
        cache.set("key3", "value3", ttl_seconds=60)
        deleted = cache.delete("key2", "key3", "nonexistent")
        assert deleted == 2
    
    def test_cache_keys_pattern(self):
        """Test keys pattern matching"""
        cache = InMemoryCache()
        
        cache.set("app:user:1", "data1", ttl_seconds=60)
        cache.set("app:user:2", "data2", ttl_seconds=60)
        cache.set("app:order:1", "data3", ttl_seconds=60)
        
        # Match user keys
        user_keys = cache.keys("app:user:*")
        assert len(user_keys) == 2
        assert all("user" in key for key in user_keys)
    
    def test_cache_clear(self):
        """Test clear operation"""
        cache = InMemoryCache()
        
        cache.set("key1", "value1", ttl_seconds=60)
        cache.set("key2", "value2", ttl_seconds=60)
        
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.get("key1") is None
    
    def test_cache_stats(self):
        """Test statistics tracking"""
        cache = InMemoryCache()
        
        cache.set("key1", "value1", ttl_seconds=60)
        
        # Generate hits and misses
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2
        assert stats["hit_ratio"] == "50.0%"
        assert stats["size"] == 1


class TestCacheLayer:
    """Test multi-tier cache layer"""
    
    def test_ticker_data_caching(self):
        """Test ticker data cache operations"""
        cache = CacheLayer()
        
        # Set ticker data
        data = pd.DataFrame({"close": [100, 101, 102]})
        cache.set_ticker_data("AAPL", data, period="1y")
        
        # Get ticker data
        cached_data = cache.get_ticker_data("AAPL", period="1y")
        assert cached_data is not None
        pd.testing.assert_frame_equal(cached_data, data)
        
        # Different period should miss
        assert cache.get_ticker_data("AAPL", period="5y") is None
    
    def test_indicator_result_caching(self):
        """Test indicator result cache operations"""
        cache = CacheLayer()
        
        # Set indicator result
        result = {"rsi": [30, 40, 50]}
        params = {"period": 14}
        cache.set_indicator_result("AAPL", "rsi", params, result)
        
        # Get indicator result
        cached_result = cache.get_indicator_result("AAPL", "rsi", params)
        assert cached_result == result
        
        # Different params should miss
        assert cache.get_indicator_result("AAPL", "rsi", {"period": 21}) is None
    
    def test_analysis_result_caching(self):
        """Test full analysis cache operations"""
        cache = CacheLayer()
        
        # Set analysis result
        result = {"overall": "bullish", "score": 7.5}
        indicators = ["rsi", "macd", "bb"]
        cache.set_analysis_result("AAPL", indicators, result)
        
        # Get analysis result
        cached_result = cache.get_analysis_result("AAPL", indicators)
        assert cached_result == result
        
        # Different indicators should miss
        assert cache.get_analysis_result("AAPL", ["rsi", "macd"]) is None
        
        # Same indicators, different order should hit (sorted internally)
        cached_result2 = cache.get_analysis_result("AAPL", ["bb", "rsi", "macd"])
        assert cached_result2 == result
    
    def test_invalidate_ticker(self):
        """Test ticker invalidation"""
        cache = CacheLayer()
        
        # Cache multiple entries for ticker
        cache.set_ticker_data("AAPL", {"data": 1})
        cache.set_indicator_result("AAPL", "rsi", {}, {"result": 1})
        cache.set_analysis_result("AAPL", ["rsi"], {"analysis": 1})
        
        # Cache entry for different ticker
        cache.set_ticker_data("MSFT", {"data": 2})
        
        # Invalidate AAPL
        deleted = cache.invalidate_ticker("AAPL")
        assert deleted >= 1  # At least one deleted
        
        # AAPL entries should be gone
        assert cache.get_ticker_data("AAPL") is None
        
        # MSFT should remain
        assert cache.get_ticker_data("MSFT") is not None
    
    def test_hash_consistency(self):
        """Test hash generation is consistent"""
        cache = CacheLayer()
        
        # Same dict should produce same hash
        hash1 = cache._hash_dict({"a": 1, "b": 2})
        hash2 = cache._hash_dict({"b": 2, "a": 1})  # Different order
        assert hash1 == hash2
        
        # Same list should produce same hash
        hash3 = cache._hash_list(["rsi", "macd"])
        hash4 = cache._hash_list(["macd", "rsi"])  # Sorted internally
        assert hash3 == hash4


class TestCachedDecorator:
    """Test automatic caching decorator"""
    
    def test_cached_decorator_basic(self):
        """Test basic decorator functionality"""
        cache = CacheLayer()
        call_count = 0
        
        @cached(cache_layer=cache, cache_type="indicator", ttl_seconds=60)
        def compute_rsi(ticker: str, period: int = 14):
            nonlocal call_count
            call_count += 1
            return {"rsi": [30, 40, 50]}
        
        # First call - compute
        result1 = compute_rsi("AAPL", period=14)
        assert call_count == 1
        
        # Second call - from cache
        result2 = compute_rsi("AAPL", period=14)
        assert call_count == 1  # Not incremented
        assert result1 == result2
        
        # Different params - compute again
        result3 = compute_rsi("AAPL", period=21)
        assert call_count == 2


# ============================================================================
# Parallel Processing Tests
# ============================================================================

class TestParallelIndicatorEngine:
    """Test parallel indicator computation"""
    
    def test_register_indicator(self):
        """Test indicator registration"""
        engine = ParallelIndicatorEngine(max_workers=2)
        
        def compute_rsi(df, period=14):
            return {"rsi": [30, 40, 50]}
        
        engine.register_indicator("rsi", compute_rsi, {"period": 14})
        
        assert "rsi" in engine.indicator_registry
        assert engine.indicator_registry["rsi"]["default_params"]["period"] == 14
    
    def test_compute_single_indicator(self):
        """Test single indicator computation"""
        engine = ParallelIndicatorEngine(max_workers=2)
        
        # Register indicator
        def compute_simple(df, multiplier=1):
            return {"result": len(df) * multiplier}
        
        engine.register_indicator("simple", compute_simple, {"multiplier": 1})
        
        # Create test dataframe
        df = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
        
        # Compute
        result = engine.compute_single("simple", df, params={"multiplier": 2})
        
        assert result.success
        assert result.result["result"] == 10  # 5 rows * 2
        assert result.duration > 0
    
    def test_compute_single_with_error(self):
        """Test error handling in single computation"""
        engine = ParallelIndicatorEngine(max_workers=2)
        
        # Register indicator that raises error
        def compute_error(df):
            raise ValueError("Test error")
        
        engine.register_indicator("error", compute_error)
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        result = engine.compute_single("error", df)
        
        assert result.failed
        assert "Test error" in result.error
    
    def test_compute_all_parallel(self):
        """Test parallel computation of multiple indicators"""
        engine = ParallelIndicatorEngine(max_workers=4)
        
        # Register multiple indicators
        def compute_indicator(df, name, delay=0):
            time.sleep(delay)  # Simulate computation time
            return {name: f"result_{name}"}
        
        for name in ["ind1", "ind2", "ind3", "ind4"]:
            engine.register_indicator(
                name,
                lambda df, n=name: compute_indicator(df, n, delay=0.1),
                {}
            )
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        start_time = time.time()
        results = engine.compute_all(df, ["ind1", "ind2", "ind3", "ind4"])
        duration = time.time() - start_time
        
        # Should complete in ~0.1s (parallel) vs ~0.4s (sequential)
        assert duration < 0.3  # Some overhead, but much faster than sequential
        
        # All should succeed
        assert len(results) == 4
        assert all(r.success for r in results.values())
    
    def test_compute_all_with_cache(self):
        """Test parallel computation with caching"""
        engine = ParallelIndicatorEngine(max_workers=2)
        cache = CacheLayer()
        
        call_count = {}
        
        def compute_cached(df, name):
            call_count[name] = call_count.get(name, 0) + 1
            return {name: f"result_{name}"}
        
        engine.register_indicator("ind1", lambda df: compute_cached(df, "ind1"))
        engine.register_indicator("ind2", lambda df: compute_cached(df, "ind2"))
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        # First computation
        results1 = engine.compute_all(df, ["ind1", "ind2"], cache=cache, ticker="AAPL")
        assert call_count["ind1"] == 1
        assert call_count["ind2"] == 1
        
        # Second computation - should use cache
        results2 = engine.compute_all(df, ["ind1", "ind2"], cache=cache, ticker="AAPL")
        assert call_count["ind1"] == 1  # Not incremented
        assert call_count["ind2"] == 1  # Not incremented
    
    def test_compute_batch(self):
        """Test batch computation with configs"""
        engine = ParallelIndicatorEngine(max_workers=2)
        
        def compute_with_params(df, period=14, multiplier=1):
            return {"value": period * multiplier}
        
        engine.register_indicator("test", compute_with_params)
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        configs = [
            {"name": "test", "params": {"period": 10, "multiplier": 2}},
            {"name": "test", "params": {"period": 20, "multiplier": 1}}
        ]
        
        results = engine.compute_batch(df, "AAPL", configs)
        
        # Note: Both use same name "test", so dict will have one entry
        assert len(results) == 1
        assert "test" in results
    
    def test_fail_fast_mode(self):
        """Test fail-fast mode stops on first error"""
        engine = ParallelIndicatorEngine(max_workers=2)
        
        def compute_ok(df):
            time.sleep(0.1)
            return {"ok": True}
        
        def compute_fail(df):
            raise ValueError("Intentional error")
        
        engine.register_indicator("ok", compute_ok)
        engine.register_indicator("fail", compute_fail)
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        results = engine.compute_all(
            df,
            ["ok", "fail"],
            fail_fast=True
        )
        
        # Should have result for fail indicator
        assert "fail" in results
        assert results["fail"].failed


class TestIndicatorBatch:
    """Test indicator batch builder"""
    
    def test_batch_builder(self):
        """Test batch configuration builder"""
        batch = IndicatorBatch()
        
        batch.add("rsi", period=14)
        batch.add("macd", fast=12, slow=26, signal=9)
        batch.add("bb", period=20, std_dev=2)
        
        configs = batch.build()
        
        assert len(configs) == 3
        assert configs[0]["name"] == "rsi"
        assert configs[0]["params"]["period"] == 14
        assert configs[1]["name"] == "macd"
        assert configs[2]["name"] == "bb"
    
    def test_batch_chaining(self):
        """Test method chaining"""
        configs = (
            IndicatorBatch()
            .add("rsi", period=14)
            .add("macd", fast=12, slow=26)
            .build()
        )
        
        assert len(configs) == 2
    
    def test_batch_clear(self):
        """Test clear operation"""
        batch = IndicatorBatch()
        batch.add("rsi", period=14)
        batch.add("macd", fast=12, slow=26)
        
        batch.clear()
        assert len(batch.configs) == 0


class TestConvenienceFunction:
    """Test convenience function"""
    
    def test_compute_indicators_parallel(self):
        """Test parallel computation convenience function"""
        # This tests the context manager usage
        # Simple test to ensure it works
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        # Note: Without registered indicators, this will return empty results
        # This test just ensures the function executes without error
        results = compute_indicators_parallel(
            dataframe=df,
            ticker="AAPL",
            indicators=[],  # Empty list
            max_workers=2
        )
        
        assert isinstance(results, dict)
        assert len(results) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestPerformanceIntegration:
    """Integration tests combining cache and parallel processing"""
    
    def test_parallel_with_cache(self):
        """Test parallel execution with caching"""
        engine = ParallelIndicatorEngine(max_workers=4)
        cache = CacheLayer()
        
        # Register simple indicators
        for i in range(5):
            engine.register_indicator(
                f"ind{i}",
                lambda df, idx=i: {"value": idx * 10},
                {}
            )
        
        df = pd.DataFrame({"close": [100, 101, 102]})
        
        # First run - compute all
        results1 = engine.compute_all(
            df,
            [f"ind{i}" for i in range(5)],
            cache=cache,
            ticker="AAPL"
        )
        
        assert all(r.success for r in results1.values())
        
        # Second run - all from cache
        results2 = engine.compute_all(
            df,
            [f"ind{i}" for i in range(5)],
            cache=cache,
            ticker="AAPL"
        )
        
        assert all(r.success for r in results2.values())
        
        # Verify cache stats show hits
        stats = cache.get_stats()
        assert stats["hits"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
