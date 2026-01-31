"""
MarketSense API Dependencies
Dependency injection for FastAPI routes
"""

from functools import lru_cache
from services.cache_service import CacheService
from services.market_service import MarketService


# Singleton instances
_cache_service = None
_market_service = None


def get_cache_service() -> CacheService:
    """
    Get or create the cache service singleton.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(default_ttl=300)  # 5 minutes
    return _cache_service


def get_market_service() -> MarketService:
    """
    Get or create the market service singleton.
    
    Returns:
        MarketService instance
    """
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
