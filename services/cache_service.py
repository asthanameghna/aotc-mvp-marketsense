"""
MarketSense Cache Service
In-memory caching with TTL for fast API responses
"""

import time
import threading
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    Thread-safe in-memory cache with TTL-based expiration.
    Designed for fast API responses while maintaining data freshness.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize the cache service.
        
        Args:
            default_ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.default_ttl = default_ttl
        self._cache = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        logger.info(f"✅ Cache service initialized with {default_ttl}s TTL")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and valid, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None

            entry = self._cache[key]
            
            # Check if expired
            if time.time() > entry['expires_at']:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache EXPIRED: {key}")
                return None

            self._hits += 1
            logger.debug(f"Cache HIT: {key}")
            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl

        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """
        Delete a specific key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED: {count} entries removed")

    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'entries': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2)
            }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cache cleanup: {len(expired_keys)} expired entries removed")
            
            return len(expired_keys)
