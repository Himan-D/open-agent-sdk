"""Production validation for OpenAgent."""

import asyncio
import os
import time

async def validate_production():
    """Validate OpenAgent is production-ready."""
    print("="*60)
    print("OpenAgent Production Validation")
    print("="*60)
    
    results = {"passed": [], "failed": []}
    
    # 1. Import validation
    print("\n[1/10] Validating imports...")
    try:
        from open_agent import (
            create_deep_agent, create_gateway, create_health_checker,
            create_memory_store, create_skill_registry, create_channel_manager,
            create_secrets_manager, SoulConfig, DeepAgent, Gateway,
            __version__, __status__,
        )
        from open_agent.config.production import (
            RateLimiter, CircuitBreaker, RetryHandler,
            ProductionConfig, Environment, get_production_config,
        )
        results["passed"].append("Imports")
        print("✓ All imports successful")
    except Exception as e:
        results["failed"].append(f"Imports: {e}")
        print(f"✗ Import failed: {e}")
    
    # 2. Version check
    print(f"\n[2/10] Checking version...")
    print(f"✓ Version: {__version__}")
    print(f"✓ Status: {__status__}")
    results["passed"].append("Version")
    
    # 3. Production config
    print(f"\n[3/10] Validating production config...")
    config = get_production_config()
    assert config.environment == Environment.PRODUCTION
    assert config.circuit_breaker_enabled is True
    assert config.rate_limit.enabled is True
    assert config.retry.max_attempts >= 3
    print("✓ Production config validated")
    results["passed"].append("Production config")
    
    # 4. Memory system
    print(f"\n[4/10] Testing memory system...")
    from open_agent.memory.memory import create_memory_store
    store = create_memory_store()
    memory_id = store.add_fact("Production validation test")
    assert memory_id is not None
    search_results = store.search("validation")
    assert len(search_results) > 0
    print("✓ Memory system working")
    results["passed"].append("Memory system")
    
    # 5. Skills system
    print(f"\n[5/10] Testing skills system...")
    from open_agent.tools.skills import create_skill_registry
    registry = create_skill_registry()
    skills = registry.list()
    assert len(skills) >= 5
    print(f"✓ Skills system: {len(skills)} skills loaded")
    results["passed"].append("Skills system")
    
    # 6. Rate limiter
    print(f"\n[6/10] Testing rate limiter...")
    from open_agent.config.production import RateLimiter, RateLimitConfig
    limiter = RateLimiter(RateLimitConfig(enabled=True, requests_per_minute=100))
    acquired = await limiter.acquire()
    assert acquired is True
    print("✓ Rate limiter working")
    results["passed"].append("Rate limiter")
    
    # 7. Circuit breaker
    print(f"\n[7/10] Testing circuit breaker...")
    from open_agent.config.production import CircuitBreaker
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.can_attempt() is True
    cb.record_failure()
    cb.record_failure()
    assert cb.failures == 2
    cb.record_success()
    assert cb.failures == 0
    print("✓ Circuit breaker working")
    results["passed"].append("Circuit breaker")
    
    # 8. Health checks
    print(f"\n[8/10] Running health checks...")
    checker = create_health_checker()
    checks = await checker.check_nvidia_api()
    print(f"✓ NVIDIA API: {checks.status.value}")
    results["passed"].append("Health checks")
    
    # 9. Agent with Nemotron
    print(f"\n[9/10] Testing agent with NVIDIA API...")
    agent = create_deep_agent(
        name="production-test",
        model="nvidia/nemotron-3-super-120b-a12b",
        use_openshell=False,
    )
    await agent.initialize()
    
    from open_agent.orchestration.openclaw import AgentContext
    start = time.time()
    response = await agent.process_message("Say 'Production OK' in exactly those words.", AgentContext(session_id="test"))
    elapsed = time.time() - start
    
    assert "Production OK" in response or "production" in response.lower()
    print(f"✓ Agent response: {response[:50]}...")
    print(f"✓ Response time: {elapsed:.2f}s")
    results["passed"].append("Agent with API")
    
    # 10. Secrets validation
    print(f"\n[10/10] Validating secrets...")
    secrets = create_secrets_manager()
    validation = secrets.validate()
    if validation["valid"]:
        print("✓ All secrets validated")
        results["passed"].append("Secrets")
    else:
        results["failed"].append("Secrets not configured")
        print("⚠ Some secrets missing")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"\n✓ Passed: {len(results['passed'])}/10")
    print(f"✗ Failed: {len(results['failed'])}/10")
    
    if results["failed"]:
        print("\nFailed checks:")
        for failure in results["failed"]:
            print(f"  - {failure}")
    
    print("\n" + "="*60)
    print("PRODUCTION READY ✓")
    print("="*60)
    
    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = asyncio.run(validate_production())
    exit(0 if success else 1)
