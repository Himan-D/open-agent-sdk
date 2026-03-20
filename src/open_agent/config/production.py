"""Production configuration for OpenAgent.

Production-ready settings with:
- Rate limiting
- Retry logic
- Timeouts
- Logging
- Monitoring
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import asyncio


class Environment(str, Enum):
    """Runtime environment."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10


@dataclass
class RetryConfig:
    """Retry configuration for API calls."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    retry_on_timeout: bool = True
    retry_on_rate_limit: bool = True


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    connect: float = 10.0
    read: float = 60.0
    write: float = 30.0
    total: float = 120.0


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "json"  # json, text
    output: str = "stdout"  # stdout, file
    file_path: Optional[str] = None
    rotation: str = "daily"  # daily, hourly, size
    max_size_mb: int = 100
    backup_count: int = 7


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    metrics_port: int = 9090
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    trace_enabled: bool = False
    trace_sample_rate: float = 0.1


@dataclass
class ProductionConfig:
    """Main production configuration."""
    environment: Environment = Environment.PRODUCTION
    
    # Rate limiting
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Retry settings
    retry: RetryConfig = field(default_factory=RetryConfig)
    
    # Timeouts
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    
    # Logging
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Security
    enable_auth: bool = True
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])
    
    # Performance
    max_concurrent_requests: int = 100
    request_queue_size: int = 1000
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds
    
    # Reliability
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_update = time.time()
        self.requests_minute = 0
        self.requests_hour = 0
        self.minute_reset = time.time()
        self.hour_reset = time.time()

    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        
        # Reset minute counter
        if now - self.minute_reset >= 60:
            self.requests_minute = 0
            self.minute_reset = now
        
        # Reset hour counter
        if now - self.hour_reset >= 3600:
            self.requests_hour = 0
            self.hour_reset = now
        
        # Refill burst tokens
        elapsed = now - self.last_update
        self.tokens = min(
            self.config.burst_size,
            self.tokens + elapsed * (self.config.requests_per_minute / 60)
        )
        self.last_update = now

    async def acquire(self) -> bool:
        """Try to acquire a token."""
        if not self.config.enabled:
            return True
        
        self._refill()
        
        if self.tokens >= 1 and self.requests_minute < self.config.requests_per_minute:
            if self.requests_hour < self.config.requests_per_hour:
                self.tokens -= 1
                self.requests_minute += 1
                self.requests_hour += 1
                return True
        
        return False

    async def wait_and_acquire(self) -> bool:
        """Wait until a token is available."""
        while not await self.acquire():
            await asyncio.sleep(0.1)
        return True


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open

    def record_success(self):
        """Record a successful call."""
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"

    def can_attempt(self) -> bool:
        """Check if a request can be attempted."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = "half_open"
                return True
            return False
        
        # half_open
        return True


class RetryHandler:
    """Handle retries with exponential backoff."""

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute(self, func, *args, **kwargs):
        """Execute a function with retries."""
        last_error = None
        delay = self.config.initial_delay

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result

            except asyncio.TimeoutError as e:
                if not self.config.retry_on_timeout:
                    raise
                last_error = e

            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_str or "rate" in error_str:
                    if not self.config.retry_on_rate_limit:
                        raise
                    delay = min(delay * self.config.exponential_base, self.config.max_delay)
                
                last_error = e

            if attempt < self.config.max_attempts - 1:
                await asyncio.sleep(delay)
                delay = min(delay * self.config.exponential_base, self.config.max_delay)

        raise last_error


# Global production config
_production_config: Optional[ProductionConfig] = None


def get_production_config() -> ProductionConfig:
    """Get production configuration."""
    global _production_config
    if _production_config is None:
        _production_config = ProductionConfig()
    return _production_config


def set_production_config(config: ProductionConfig) -> None:
    """Set production configuration."""
    global _production_config
    _production_config = config


def is_production() -> bool:
    """Check if running in production."""
    config = get_production_config()
    return config.environment == Environment.PRODUCTION
