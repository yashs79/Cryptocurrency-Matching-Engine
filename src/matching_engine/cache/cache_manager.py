"""
Cache Manager

In-memory caching with TTL support for high-performance data access.
"""

from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta, UTC
from functools import lru_cache
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    value: Any
    expires_at: datetime
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return datetime.now(UTC) >= self.expires_at


class CacheManager:
    """
    High-performance in-memory cache with TTL support.
    
    Features:
    - TTL-based expiration
    - Automatic cleanup
    - Cache statistics
    - Multiple cache namespaces
    """
    
    def __init__(self, default_ttl_seconds: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_ttl_seconds: Default TTL in seconds (default: 5 minutes)
        """
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        
        logger.info(f"CacheManager initialized with default TTL: {default_ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        self._sets += 1
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            self._deletes += 1
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "deletes": self._deletes,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
    
    # Convenience methods for specific data types
    
    def get_order(self, order_id: str):
        """Get order from cache"""
        return self.get(f"order:{order_id}")
    
    def set_order(self, order_id: str, order: Any, ttl_seconds: int = 300):
        """Cache order"""
        self.set(f"order:{order_id}", order, ttl_seconds)
    
    def delete_order(self, order_id: str):
        """Remove order from cache"""
        self.delete(f"order:{order_id}")
    
    def get_user_orders(self, user_id: str) -> Optional[List]:
        """Get user orders from cache"""
        return self.get(f"user_orders:{user_id}")
    
    def set_user_orders(self, user_id: str, orders: List, ttl_seconds: int = 60):
        """Cache user orders"""
        self.set(f"user_orders:{user_id}", orders, ttl_seconds)
    
    def delete_user_orders(self, user_id: str):
        """Remove user orders from cache"""
        self.delete(f"user_orders:{user_id}")
    
    def get_orderbook(self, symbol: str):
        """Get order book from cache"""
        return self.get(f"orderbook:{symbol}")
    
    def set_orderbook(self, symbol: str, orderbook: Any, ttl_seconds: int = 5):
        """Cache order book (short TTL for real-time data)"""
        self.set(f"orderbook:{symbol}", orderbook, ttl_seconds)
    
    def get_trade(self, trade_id: str):
        """Get trade from cache"""
        return self.get(f"trade:{trade_id}")
    
    def set_trade(self, trade_id: str, trade: Any, ttl_seconds: int = 600):
        """Cache trade"""
        self.set(f"trade:{trade_id}", trade, ttl_seconds)
    
    def get_market_stats(self, symbol: str):
        """Get market stats from cache"""
        return self.get(f"market_stats:{symbol}")
    
    def set_market_stats(self, symbol: str, stats: Any, ttl_seconds: int = 30):
        """Cache market stats"""
        self.set(f"market_stats:{symbol}", stats, ttl_seconds)


# Global cache manager instance
cache_manager = CacheManager(default_ttl_seconds=300)
