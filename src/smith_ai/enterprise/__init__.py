"""Enterprise Infrastructure - Rate limiting, caching, observability, secrets.

Features:
- Rate limiting (token bucket, leaky bucket)
- Response caching (Redis, memory)
- Observability (OpenTelemetry, metrics, tracing)
- Secrets management
- Circuit breakers
- Retry policies
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import functools
import structlog

logger = structlog.get_logger(__name__)


class RateLimitStrategy(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET


class TokenBucket:
    """Token bucket rate limiter."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens."""
        async with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now


class RateLimiter:
    """Multi-level rate limiter."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        rpm_tokens = config.requests_per_minute
        rpm_rate = rpm_tokens / 60.0
        self._minute_bucket = TokenBucket(rpm_tokens, rpm_rate)
        
        rph_tokens = config.requests_per_hour
        rph_rate = rph_tokens / 3600.0
        self._hour_bucket = TokenBucket(rph_tokens, rph_rate)
        
        rpd_tokens = config.requests_per_day
        rpd_rate = rpd_tokens / 86400.0
        self._day_bucket = TokenBucket(rpd_tokens, rpd_rate)
    
    async def acquire(self) -> bool:
        """Try to acquire rate limit slot."""
        if not await self._minute_bucket.acquire():
            raise RateLimitExceeded("Minute rate limit exceeded")
        
        if not await self._hour_bucket.acquire():
            raise RateLimitExceeded("Hour rate limit exceeded")
        
        if not await self._day_bucket.acquire():
            raise RateLimitExceeded("Daily rate limit exceeded")
        
        return True
    
    async def wait_for_slot(self, max_wait: float = 60) -> bool:
        """Wait for a rate limit slot."""
        start = time.time()
        
        while time.time() - start < max_wait:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        
        raise RateLimitExceeded(f"Waited more than {max_wait}s for rate limit")


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    async def can_execute(self) -> bool:
        """Check if execution is allowed."""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and \
                   time.time() - self._last_failure_time > self.config.timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            
            return True
    
    async def record_success(self):
        """Record successful execution."""
        async with self._lock:
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._success_count = 0
    
    async def record_failure(self):
        """Record failed execution."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker."""
        if not await self.can_execute():
            raise CircuitBreakerOpen("Circuit breaker is open")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self.record_success()
            return result
        
        except Exception as e:
            await self.record_failure()
            raise


@dataclass
class RetryConfig:
    """Configuration for retry policy."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retry_on: List[type] = field(default_factory=lambda: [Exception])


async def retry(func: Callable, config: RetryConfig, *args, **kwargs) -> Any:
    """Execute function with retry logic."""
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        except Exception as e:
            last_exception = e
            
            should_retry = any(isinstance(e, retry_type) for retry_type in config.retry_on)
            
            if not should_retry or attempt == config.max_attempts - 1:
                raise
            
            logger.warning(
                "retry_attempt",
                attempt=attempt + 1,
                max_attempts=config.max_attempts,
                delay=delay,
                error=str(e)
            )
            
            await asyncio.sleep(delay)
            delay = min(delay * config.exponential_base, config.max_delay)
    
    raise last_exception


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class MemoryCache(CacheBackend):
    """In-memory cache for single-instance deployments."""
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Tuple[str, Optional[float]]] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or time.time() < expiry:
                    return value
                del self._cache[key]
            return None
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        async with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1] or 0)
                del self._cache[oldest_key]
            
            expiry = None
            if ttl:
                expiry = time.time() + ttl
            
            self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None


class RedisCache(CacheBackend):
    """Redis cache backend for distributed caching."""
    
    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "smithai:"):
        self.url = url
        self.prefix = prefix
        self._client: Optional[Any] = None
    
    async def _ensure_client(self):
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.from_url(self.url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[str]:
        await self._ensure_client()
        return await self._client.get(f"{self.prefix}{key}")
    
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        await self._ensure_client()
        if ttl:
            await self._client.setex(f"{self.prefix}{key}", ttl, value)
        else:
            await self._client.set(f"{self.prefix}{key}", value)
    
    async def delete(self, key: str) -> None:
        await self._ensure_client()
        await self._client.delete(f"{self.prefix}{key}")
    
    async def exists(self, key: str) -> bool:
        await self._ensure_client()
        return await self._client.exists(f"{self.prefix}{key}") > 0


def cached(
    backend: CacheBackend,
    key_prefix: str = "",
    ttl: Optional[int] = 3600,
    cache_condition: Optional[Callable] = None,
):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            
            if cache_condition and not cache_condition(*args, **kwargs):
                return await func(*args, **kwargs)
            
            cached_value = await backend.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            
            result = await func(*args, **kwargs)
            await backend.set(cache_key, json.dumps(result), ttl)
            
            return result
        
        return wrapper
    return decorator


class SecretsManager:
    """Manage secrets securely."""
    
    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._loaded = False
    
    def load_env(self, prefix: str = "") -> None:
        """Load secrets from environment variables."""
        import os
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
            secret_name = key.removeprefix(prefix).lower()
            self._secrets[secret_name] = value
        
        self._loaded = True
        logger.info("secrets_loaded", count=len(self._secrets))
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret."""
        return self._secrets.get(key.lower(), default)
    
    def set(self, key: str, value: str) -> None:
        """Set a secret."""
        self._secrets[key.lower()] = value
    
    def mask(self, value: str) -> str:
        """Mask a secret value for logging."""
        if len(value) <= 8:
            return "***"
        return value[:4] + "***" + value[-4:]


class Observability:
    """Observability hooks for agents."""
    
    def __init__(self):
        self._traces: List[Dict[str, Any]] = []
        self._metrics: Dict[str, int] = {}
        self._logs: List[Dict[str, Any]] = []
    
    def trace(
        self,
        operation: str,
        agent: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a trace."""
        trace = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "agent": agent,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        }
        self._traces.append(trace)
        
        key = f"{agent}.{operation}"
        self._metrics[key] = self._metrics.get(key, 0) + 1
    
    def log(
        self,
        level: str,
        message: str,
        agent: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log an event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "agent": agent,
            **kwargs
        }
        self._logs.append(log_entry)
        
        level_method = getattr(logger, level, logger.info)
        level_method(message, agent=agent, **kwargs)
    
    def get_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent traces."""
        return self._traces[-limit:]
    
    def get_metrics(self) -> Dict[str, int]:
        """Get metrics."""
        return self._metrics.copy()
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs."""
        return self._logs[-limit:]
    
    def clear(self) -> None:
        """Clear all data."""
        self._traces.clear()
        self._metrics.clear()
        self._logs.clear()


@dataclass
class EnterpriseConfig:
    """Configuration for enterprise features."""
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    cache_ttl: int = 3600
    observability_enabled: bool = True


class EnterpriseManager:
    """Manage enterprise infrastructure."""
    
    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self.config = config or EnterpriseConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.circuit_breaker = CircuitBreaker(self.config.circuit_breaker)
        self.cache = MemoryCache()
        self.secrets = SecretsManager()
        self.observability = Observability()
    
    def load_secrets(self) -> None:
        """Load secrets from environment."""
        self.secrets.load_env(prefix="SMITHAI_")
    
    async def with_rate_limit(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with rate limiting."""
        await self.rate_limiter.acquire()
        return await func(*args, **kwargs)
    
    async def with_circuit_breaker(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with circuit breaker."""
        return await self.circuit_breaker.execute(func, *args, **kwargs)
    
    async def with_cache(self, key: str, func: Callable, ttl: Optional[int] = None) -> Any:
        """Execute with caching."""
        cached_value = await self.cache.get(key)
        if cached_value:
            return json.loads(cached_value)
        
        result = await func()
        await self.cache.set(key, json.dumps(result), ttl or self.config.cache_ttl)
        return result


__all__ = [
    "RateLimitConfig",
    "RateLimitStrategy",
    "RateLimiter",
    "RateLimitExceeded",
    "TokenBucket",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitState",
    "RetryConfig",
    "retry",
    "CacheBackend",
    "MemoryCache",
    "RedisCache",
    "cached",
    "SecretsManager",
    "Observability",
    "EnterpriseConfig",
    "EnterpriseManager",
]
