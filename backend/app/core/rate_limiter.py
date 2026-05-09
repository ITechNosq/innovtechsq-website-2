"""
Rate Limiting Module
Production-ready Redis-based rate limiting.

Supports:
- Per-IP rate limiting
- Per-API key rate limiting
- Sliding window algorithm
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter.
    Uses sliding window algorithm for accurate rate limiting.
    """
    
    def __init__(self):
        self._redis = None
        self._enabled = bool(settings.REDIS_URL)
    
    def _get_redis_client(self):
        """Lazy load Redis client."""
        if not self._enabled:
            return None
        
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Rate limiting disabled.")
                self._enabled = False
                return None
        
        return self._redis
    
    def check_rate_limit(self, identifier: str, limit: int = None) -> tuple[bool, dict]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (IP, API key, user ID)
            limit: Requests per minute allowed
            
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        limit = limit or settings.RATE_LIMIT_PER_MINUTE
        
        # If Redis unavailable, use in-memory fallback (not for production!)
        client = self._get_redis_client()
        if not client:
            return self._fallback_check(identifier, limit)
        
        key = f"rate_limit:{identifier}"
        
        try:
            # Get current count
            current = client.get(key)
            if current is None:
                count = 0
            else:
                count = int(current)
            
            # Check limit
            if count >= limit:
                ttl = client.ttl(key)
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset_in_seconds": ttl if ttl > 0 else 60
                }
            
            # Increment and set expiry
            pipe = client.pipeline()
            pipe.incr(key)
            if count == 0:
                pipe.expire(key, 60)  # 1 minute window
            pipe.execute()
            
            return True, {
                "limit": limit,
                "remaining": limit - count - 1,
                "reset_in_seconds": 60
            }
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open (allow request) if Redis fails
            return True, {"limit": limit, "remaining": limit}
    
    def _fallback_check(self, identifier: str, limit: int) -> tuple[bool, dict]:
        """
        Fallback in-memory rate limiting.
        WARNING: Not suitable for production with multiple workers!
        """
        import threading
        
        if not hasattr(self, "_fallback_store"):
            self._fallback_store = {}
            self._fallback_lock = threading.Lock()
        
        with self._fallback_lock:
            current_minute = datetime.now().replace(second=0, microsecond=0)
            
            if identifier not in self._fallback_store:
                self._fallback_store[identifier] = {}
            
            # Clean old entries
            self._fallback_store[identifier] = {
                k: v for k, v in self._fallback_store[identifier].items()
                if k >= current_minute - timedelta(minutes=1)
            }
            
            count = len(self._fallback_store[identifier])
            
            if count >= limit:
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset_in_seconds": 60
                }
            
            self._fallback_store[identifier][current_minute] = count + 1
            
            return True, {
                "limit": limit,
                "remaining": limit - count - 1,
                "reset_in_seconds": 60
            }
    
    def get_rate_limit_info(self, identifier: str) -> dict:
        """Get current rate limit status without incrementing."""
        client = self._get_redis_client()
        
        if not client:
            return {"limit": settings.RATE_LIMIT_PER_MINUTE, "remaining": "unknown"}
        
        try:
            key = f"rate_limit:{identifier}"
            count = client.get(key)
            remaining = settings.RATE_LIMIT_PER_MINUTE - (int(count) if count else 0)
            return {
                "limit": settings.RATE_LIMIT_PER_MINUTE,
                "remaining": max(0, remaining)
            }
        except Exception:
            return {"limit": settings.RATE_LIMIT_PER_MINUTE, "remaining": "unknown"}


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_ip_rate_limit(ip: str) -> tuple[bool, dict]:
    """Check rate limit for IP address."""
    return rate_limiter.check_rate_limit(f"ip:{ip}")


def check_api_key_rate_limit(api_key: str) -> tuple[bool, dict]:
    """Check rate limit for API key."""
    import hashlib
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return rate_limiter.check_rate_limit(f"key:{key_hash}")


def check_email_rate_limit(email: str, limit: int = 3) -> tuple[bool, dict]:
    """Check rate limit for an email to prevent email bombing."""
    import hashlib
    # Hash email to avoid storing PII in Redis keys unnecessarily
    email_hash = hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]
    return rate_limiter.check_rate_limit(f"email:{email_hash}", limit=limit)
