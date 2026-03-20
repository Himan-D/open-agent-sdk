"""Tests for OpenAgent."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from open_agent.config.production import (
    RateLimiter,
    CircuitBreaker,
    RetryHandler,
    ProductionConfig,
    Environment,
)


class TestRateLimiter:
    """Tests for rate limiter."""

    @pytest.fixture
    def rate_limiter(self):
        from open_agent.config.production import RateLimitConfig
        config = RateLimitConfig(
            enabled=True,
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5,
        )
        return RateLimiter(config)

    @pytest.mark.asyncio
    async def test_acquire_success(self, rate_limiter):
        """Test successful token acquisition."""
        result = await rate_limiter.acquire()
        assert result is True
        assert rate_limiter.tokens < 5

    @pytest.mark.asyncio
    async def test_acquire_exhausted(self, rate_limiter):
        """Test token exhaustion."""
        # Exhaust all tokens
        for _ in range(5):
            await rate_limiter.acquire()
        
        # Should fail now
        result = await rate_limiter.acquire()
        assert result is False

    @pytest.mark.asyncio
    async def test_wait_and_acquire(self, rate_limiter):
        """Test wait and acquire."""
        result = await rate_limiter.wait_and_acquire()
        assert result is True


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_initial_state(self):
        """Test circuit breaker starts closed."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == "closed"
        assert cb.can_attempt() is True

    def test_opens_after_threshold(self):
        """Test circuit opens after threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == "open"
        assert cb.can_attempt() is False

    def test_resets_on_success(self):
        """Test circuit resets on success."""
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb.failures == 0
        assert cb.state == "closed"


class TestRetryHandler:
    """Tests for retry handler."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution without retry."""
        from open_agent.config.production import RetryConfig
        config = RetryConfig(max_attempts=3)
        handler = RetryHandler(config)
        
        async def success():
            return "success"
        
        result = await handler.execute(success)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry on temporary failure."""
        from open_agent.config.production import RetryConfig
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        attempts = 0
        
        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = await handler.execute(flaky)
        assert result == "success"
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """Test max attempts exceeded."""
        from open_agent.config.production import RetryConfig
        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        handler = RetryHandler(config)
        
        async def always_fail():
            raise Exception("Permanent error")
        
        with pytest.raises(Exception) as exc_info:
            await handler.execute(always_fail)
        
        assert "Permanent error" in str(exc_info.value)


class TestProductionConfig:
    """Tests for production configuration."""

    def test_default_config(self):
        """Test default production config."""
        config = ProductionConfig()
        
        assert config.environment == Environment.PRODUCTION
        assert config.rate_limit.enabled is True
        assert config.retry.max_attempts == 3
        assert config.circuit_breaker_enabled is True

    def test_custom_config(self):
        """Test custom production config."""
        config = ProductionConfig(environment=Environment.DEVELOPMENT)
        config.rate_limit.requests_per_minute = 100
        config.retry.max_attempts = 5
        
        assert config.environment == Environment.DEVELOPMENT
        assert config.rate_limit.requests_per_minute == 100
        assert config.retry.max_attempts == 5


class TestMemoryStore:
    """Tests for memory store."""

    def test_memory_entry(self):
        """Test memory entry creation."""
        from open_agent.memory.memory import MemoryEntry
        import time
        
        entry = MemoryEntry(
            id="test_1",
            content="Test content",
            timestamp=time.time(),
            type="fact",
        )
        
        assert entry.id == "test_1"
        assert entry.content == "Test content"
        assert entry.type == "fact"


class TestSkills:
    """Tests for skills system."""

    def test_skill_creation(self):
        """Test skill creation."""
        from open_agent.tools.skills import Skill
        
        skill = Skill(
            name="test_skill",
            description="A test skill",
            instructions="Do something",
        )
        
        assert skill.name == "test_skill"
        assert skill.enabled is True
        assert skill.category == "general"


class TestSoulConfig:
    """Tests for SoulConfig."""

    def test_soul_config_creation(self):
        """Test SoulConfig creation."""
        from open_agent.orchestration.openclaw import SoulConfig
        
        soul = SoulConfig(
            name="Test Agent",
            emoji="",
            team="Test",
            responsibilities=["Test task"],
            constraints=["Test constraint"],
        )
        
        assert soul.name == "Test Agent"
        assert len(soul.responsibilities) == 1
        assert len(soul.constraints) == 1


class TestChannelConfig:
    """Tests for channel configuration."""

    def test_channel_types(self):
        """Test channel types."""
        from open_agent.channels.channel_manager import ChannelType
        
        assert ChannelType.SLACK.value == "slack"
        assert ChannelType.DISCORD.value == "discord"
        assert ChannelType.TELEGRAM.value == "telegram"


class TestHealthChecker:
    """Tests for health checker."""

    def test_health_status(self):
        """Test health status enum."""
        from open_agent.core.health import HealthStatus
        
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
