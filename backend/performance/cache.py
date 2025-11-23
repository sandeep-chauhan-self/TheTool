"""
Multi-tier Caching Layer

Part 4: Architecture Blueprint
PERFORMANCE_ARCHITECTURE_001: Caching Layer

Implements in-memory caching with optional Redis backend.
Provides significant performance improvements through data reuse.
"""

import hashlib
import pickle
import time
import json
from typing import Optional, Any, Callable
from datetime import timedelta
from functools import wraps
from collections import OrderedDict
import logging
import threading

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration"""
    # TTL (Time To Live) in seconds
    TICKER_DATA_TTL = 300        # 5 minutes - Market data
    INDICATOR_RESULT_TTL = 600   # 10 minutes - Indicator calculations
    ANALYSIS_RESULT_TTL = 3600   # 1 hour - Full analysis
    
    # Cache keys
    KEY_PREFIX = "thetool"
    TICKER_DATA_KEY = "{prefix}:ticker:{ticker}:{period}"
    INDICATOR_KEY = "{prefix}:indicator:{ticker}:{indicator}:{params_hash}"
    ANALYSIS_KEY = "{prefix}:analysis:{ticker}:{indicators_hash}"
    
    # LRU cache size (for in-memory)
    MAX_CACHE_SIZE = 1000


class InMemoryCache:
    """
    Thread-safe in-memory LRU cache
    
    Used as fallback when Redis is not available.
    Implements LRU (Least Recently Used) eviction.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                
                # Check expiry
                if expiry > time.time():
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    logger.debug(f"Cache HIT: {key}")
                    return value
                else:
                    # Expired
                    del self.cache[key]
            
            self.misses += 1
            logger.debug(f"Cache MISS: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in cache with TTL"""
        with self.lock:
            expiry = time.time() + ttl_seconds
            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)
            
            # Evict oldest if over max size
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"Cache EVICT: {oldest_key}")
    
    def delete(self, *keys: str) -> int:
        """Delete keys from cache"""
        with self.lock:
            deleted = 0
            for key in keys:
                if key in self.cache:
                    del self.cache[key]
                    deleted += 1
            return deleted
    
    def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern (wildcard support with proper positioning)"""
        with self.lock:
            # Parse pattern: split on * to get parts, track anchoring
            pattern_parts = pattern.split('*')
            start_anchored = not pattern.startswith('*')  # Pattern starts with literal
            end_anchored = not pattern.endswith('*')      # Pattern ends with literal
            
            matching_keys = []
            
            for key in self.cache.keys():
                # Filter empty parts
                parts = [p for p in pattern_parts if p]
                
                if not parts:
                    # Pattern is just * or **
                    matching_keys.append(key)
                    continue
                
                # Check start anchor
                if start_anchored and not key.startswith(parts[0]):
                    continue
                
                # Check end anchor
                if end_anchored and not key.endswith(parts[-1]):
                    continue
                
                # Check intermediate parts are present in order
                cursor = 0
                match = True
                for i, part in enumerate(parts):
                    idx = key.find(part, cursor)
                    if idx == -1:
                        match = False
                        break
                    cursor = idx + len(part)
                
                if match:
                    matching_keys.append(key)
            
            return matching_keys
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_ratio = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": f"{hit_ratio:.1f}%",
                "total_requests": total_requests
            }


class CacheLayer:
    """
    Multi-tier caching layer
    
    Tier 1: Ticker data (5 min TTL)
    Tier 2: Indicator results (10 min TTL)  
    Tier 3: Full analysis (1 hour TTL)
    
    Uses in-memory cache by default, with optional Redis backend.
    """
    
    def __init__(self, backend: Optional[Any] = None):
        """
        Initialize cache layer
        
        Args:
            backend: Optional cache backend (InMemoryCache or Redis client)
                    If None, uses default InMemoryCache
        """
        self.backend = backend or InMemoryCache(max_size=CacheConfig.MAX_CACHE_SIZE)
        self.config = CacheConfig()
    
    def get_ticker_data(self, ticker: str, period: str = "1y") -> Optional[Any]:
        """Get cached ticker data"""
        key = self.config.TICKER_DATA_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            period=period
        )
        return self._get(key)
    
    def set_ticker_data(self, ticker: str, data: Any, period: str = "1y") -> None:
        """Cache ticker data"""
        key = self.config.TICKER_DATA_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            period=period
        )
        self._set(key, data, self.config.TICKER_DATA_TTL)
    
    def get_indicator_result(
        self,
        ticker: str,
        indicator: str,
        params: dict
    ) -> Optional[Any]:
        """Get cached indicator result"""
        params_hash = self._hash_dict(params)
        key = self.config.INDICATOR_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            indicator=indicator,
            params_hash=params_hash
        )
        return self._get(key)
    
    def set_indicator_result(
        self,
        ticker: str,
        indicator: str,
        params: dict,
        result: Any
    ) -> None:
        """Cache indicator result"""
        params_hash = self._hash_dict(params)
        key = self.config.INDICATOR_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            indicator=indicator,
            params_hash=params_hash
        )
        self._set(key, result, self.config.INDICATOR_RESULT_TTL)
    
    def get_analysis_result(
        self,
        ticker: str,
        indicators: list[str]
    ) -> Optional[Any]:
        """Get cached full analysis"""
        indicators_hash = self._hash_list(sorted(indicators))
        key = self.config.ANALYSIS_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            indicators_hash=indicators_hash
        )
        return self._get(key)
    
    def set_analysis_result(
        self,
        ticker: str,
        indicators: list[str],
        result: Any
    ) -> None:
        """Cache full analysis"""
        indicators_hash = self._hash_list(sorted(indicators))
        key = self.config.ANALYSIS_KEY.format(
            prefix=self.config.KEY_PREFIX,
            ticker=ticker,
            indicators_hash=indicators_hash
        )
        self._set(key, result, self.config.ANALYSIS_RESULT_TTL)
    
    def invalidate_ticker(self, ticker: str) -> int:
        """Invalidate all cache entries for a ticker"""
        pattern = f"{self.config.KEY_PREFIX}:*:{ticker}:*"
        keys = self.backend.keys(pattern)
        if keys:
            return self.backend.delete(*keys)
        return 0
    
    def clear(self) -> None:
        """Clear all cache entries"""
        if hasattr(self.backend, 'clear'):
            self.backend.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        if hasattr(self.backend, 'get_stats'):
            return self.backend.get_stats()
        return {"error": "Stats not available for this backend"}
    
    def _get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            return self.backend.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def _set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set value in cache"""
        try:
            self.backend.set(key, value, ttl_seconds)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    def _hash_dict(self, d: dict) -> str:
        """Create hash of dictionary"""
        content = str(sorted(d.items())).encode()
        return hashlib.md5(content).hexdigest()[:8]
    
    def _hash_list(self, lst: list) -> str:
        """Create hash of list"""
        content = str(sorted(lst)).encode()
        return hashlib.md5(content).hexdigest()[:8]


def cached(
    cache_layer: Optional[CacheLayer] = None,
    cache_type: str = "analysis",
    ttl_seconds: Optional[int] = None
) -> Callable:
    """
    Decorator for automatic caching
    
    Usage:
        cache = CacheLayer()
        
        @cached(cache_layer=cache, cache_type="indicator", ttl_seconds=600)
        def compute_rsi(ticker: str, df, period=14):
            # expensive computation
            return result
    
    Args:
        cache_layer: CacheLayer instance (creates new if None)
        cache_type: Type of cache ("ticker", "indicator", "analysis")
        ttl_seconds: Custom TTL in seconds (uses default if None)
    """
    # Map cache_type to CacheConfig attribute names
    TTL_MAPPING = {
        "ticker": "TICKER_DATA_TTL",
        "indicator": "INDICATOR_RESULT_TTL",
        "analysis": "ANALYSIS_RESULT_TTL",
    }
    
    def decorator(func: Callable) -> Callable:
        nonlocal cache_layer
        if cache_layer is None:
            cache_layer = CacheLayer()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments with deterministic serialization
            key_parts = [func.__name__]
            
            # Serialize args deterministically
            for arg in args:
                try:
                    # Try JSON serialization first (deterministic)
                    serialized = json.dumps(arg, separators=(',', ':'), sort_keys=True, default=str)
                except (TypeError, ValueError):
                    # Fall back to repr for non-JSON-serializable objects
                    serialized = repr(arg)
                key_parts.append(serialized)
            
            # Serialize kwargs deterministically
            for k, v in sorted(kwargs.items()):
                try:
                    serialized = json.dumps(v, separators=(',', ':'), sort_keys=True, default=str)
                except (TypeError, ValueError):
                    serialized = repr(v)
                key_parts.append(f"{k}={serialized}")
            
            # Build cache key with deterministic separator
            key_base = f"{CacheConfig.KEY_PREFIX}:{cache_type}:" + "||".join(key_parts)
            
            # If key is too long, use hash instead
            if len(key_base) > 255:
                key_hash = hashlib.sha256(key_base.encode()).hexdigest()
                cache_key = f"{CacheConfig.KEY_PREFIX}:{cache_type}:{key_hash}"
            else:
                cache_key = key_base
            
            # Try cache
            cached_result = cache_layer._get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute
            result = func(*args, **kwargs)
            
            # Determine TTL using mapping with fallback
            ttl_attr = TTL_MAPPING.get(cache_type, "ANALYSIS_RESULT_TTL")
            ttl = ttl_seconds or getattr(CacheConfig, ttl_attr, 300)
            cache_layer._set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
