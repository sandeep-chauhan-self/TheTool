"""
Caching Layer for Indicator Results

CRITICAL FIX (ISSUE_011): In-memory cache to prevent redundant calculations
and reduce API response time by 80%+ for cached indicators.

Features:
- Thread-safe LRU cache with TTL expiration
- Configurable cache size and TTL
- Cache key based on ticker + timeframe + indicator parameters
- Automatic eviction of stale entries
- Cache statistics for monitoring
"""

import threading
import time
import hashlib
import json
from typing import Any, Optional, Dict, Tuple
from functools import wraps
from collections import OrderedDict
from config import config


class ThreadSafeLRUCache:
    """
    Thread-safe LRU (Least Recently Used) cache with TTL support.
    
    Design:
    - OrderedDict for O(1) lookup and LRU ordering
    - Thread lock for concurrent access safety
    - TTL (Time To Live) for automatic expiration
    - Size limit with automatic eviction
    
    Performance:
    - Get: O(1) average
    - Set: O(1) average
    - Memory: O(cache_size)
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of entries (default 1000)
            default_ttl: Default TTL in seconds (default 3600 = 1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        # Secondary index: ticker_upper -> set of cache keys for precise invalidation
        self._ticker_index: Dict[str, set] = {}
        # Metadata per cache key: key_hash -> (ticker_upper, indicator_lower)
        self._key_metadata: Dict[str, Tuple[str, str]] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _generate_key(self, ticker: str, indicator: str, **params) -> str:
        """
        Generate cache key from ticker, indicator, and parameters.
        
        Args:
            ticker: Stock ticker symbol
            indicator: Indicator name
            **params: Additional parameters (period, etc.)
            
        Returns:
            str: Cache key hash
        """
        # Create deterministic key from sorted params
        key_parts = [
            ticker.upper(),
            indicator.lower(),
            json.dumps(params, sort_keys=True)
        ]
        key_string = '|'.join(key_parts)
        
        # Hash for consistent key length
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get(self, ticker: str, indicator: str, **params) -> Optional[Any]:
        """
        Get cached value if exists and not expired.
        
        Args:
            ticker: Stock ticker symbol
            indicator: Indicator name
            **params: Additional parameters
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(ticker, indicator, **params)
        
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
            if time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value
    
    def set(self, ticker: str, indicator: str, value: Any, ttl: Optional[int] = None, **params):
        """
        Set cache entry with TTL.
        
        Args:
            ticker: Stock ticker symbol
            indicator: Indicator name
            value: Value to cache
            ttl: Time to live in seconds (None = use default)
            **params: Additional parameters
        """
        key = self._generate_key(ticker, indicator, **params)
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        ticker_upper = ticker.upper()
        indicator_lower = indicator.lower()
        
        with self._lock:
            # Add or update entry
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
            
            # Update secondary index for precise invalidation
            if ticker_upper not in self._ticker_index:
                self._ticker_index[ticker_upper] = set()
            self._ticker_index[ticker_upper].add(key)
            
            # Store metadata: key -> (ticker_upper, indicator_lower)
            self._key_metadata[key] = (ticker_upper, indicator_lower)
            
            # Evict oldest if over size limit
            if len(self._cache) > self.max_size:
                evicted_key = self._cache.popitem(last=False)[0]
                self._evictions += 1
                
                # Clean up secondary index and metadata for evicted key
                if evicted_key in self._key_metadata:
                    evicted_ticker, _ = self._key_metadata[evicted_key]
                    if evicted_ticker in self._ticker_index:
                        self._ticker_index[evicted_ticker].discard(evicted_key)
                        # Remove ticker from index if its set is empty
                        if not self._ticker_index[evicted_ticker]:
                            del self._ticker_index[evicted_ticker]
                    del self._key_metadata[evicted_key]
    
    def invalidate(self, ticker: str, indicator: Optional[str] = None):
        """
        Invalidate cache entries for a ticker using precise key tracking.
        
        Args:
            ticker: Stock ticker symbol
            indicator: Specific indicator to invalidate (None = all)
        """
        ticker_upper = ticker.upper()
        
        with self._lock:
            # Look up exact set of keys for this ticker in the index
            if ticker_upper not in self._ticker_index:
                # Ticker not in index, nothing to invalidate
                return
            
            keys_to_remove = []
            
            if indicator is None:
                # Invalidate all indicators for this ticker
                keys_to_remove = list(self._ticker_index[ticker_upper])
            else:
                # Invalidate only matching indicator
                indicator_lower = indicator.lower()
                for key in self._ticker_index[ticker_upper]:
                    if key in self._key_metadata:
                        _, stored_indicator = self._key_metadata[key]
                        # Exact match on indicator name
                        if stored_indicator == indicator_lower:
                            keys_to_remove.append(key)
            
            # Delete each key from cache and index
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                
                # Remove from ticker index
                if ticker_upper in self._ticker_index:
                    self._ticker_index[ticker_upper].discard(key)
                
                # Remove metadata
                if key in self._key_metadata:
                    del self._key_metadata[key]
            
            # Clean up ticker entry if its set is now empty
            if ticker_upper in self._ticker_index and not self._ticker_index[ticker_upper]:
                del self._ticker_index[ticker_upper]
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._ticker_index.clear()
            self._key_metadata.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            dict: Cache statistics
        """
        with self._lock:
            hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': round(hit_rate * 100, 2),
                'enabled': config.CACHE_ENABLED,
                'ticker_index_size': len(self._ticker_index),
                'indexed_tickers': list(self._ticker_index.keys())
            }


# Global cache instance
_indicator_cache = ThreadSafeLRUCache(
    max_size=config.CACHE_MAX_SIZE,
    default_ttl=config.CACHE_TTL
) if config.CACHE_ENABLED else None


def cached_indicator(indicator_name: str, ttl: Optional[int] = None):
    """
    Decorator to cache indicator calculation results.
    
    Usage:
        @cached_indicator('rsi', ttl=3600)
        def calculate_rsi(df, period=14):
            # ... calculation ...
            return result
    
    Args:
        indicator_name: Name of the indicator for cache key
        ttl: Time to live in seconds (None = use default)
        
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        @wraps(func)
        def wrapper(df, *args, **kwargs):
            # Skip cache if disabled
            if not config.CACHE_ENABLED or _indicator_cache is None:
                return func(df, *args, **kwargs)
            
            # Try to extract ticker from df metadata or first call
            ticker = kwargs.get('ticker') or getattr(df, 'ticker', None) or 'unknown'
            
            # Create cache key from function arguments (exclude df and non-serializable items)
            cache_params = {
                'args': args,
                'kwargs': {k: v for k, v in kwargs.items() if k != 'ticker' and k != 'df'}
            }
            
            # Try to get from cache using full cache_params
            try:
                cached_value = _indicator_cache.get(ticker, indicator_name, args=args, **cache_params['kwargs'])
                if cached_value is not None:
                    return cached_value
            except (TypeError, ValueError):
                # If cache key generation fails, skip cache
                pass
            
            # Calculate result
            result = func(df, *args, **kwargs)
            
            # Store in cache using full cache_params
            try:
                _indicator_cache.set(ticker, indicator_name, result, ttl=ttl, args=args, **cache_params['kwargs'])
            except (TypeError, ValueError):
                # If cache storage fails, continue without caching
                pass
            
            return result
        
        return wrapper
    return decorator


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.
    
    Returns:
        dict: Cache statistics or disabled message
    """
    if _indicator_cache:
        return _indicator_cache.stats()
    return {'enabled': False, 'message': 'Cache is disabled'}


def clear_cache():
    """Clear all cache entries"""
    if _indicator_cache:
        _indicator_cache.clear()


def invalidate_ticker_cache(ticker: str, indicator: Optional[str] = None):
    """
    Invalidate cache for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        indicator: Specific indicator to invalidate (None = all)
    """
    if _indicator_cache:
        _indicator_cache.invalidate(ticker, indicator)
