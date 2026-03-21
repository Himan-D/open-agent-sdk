"""Comprehensive tests for SmithAI enterprise features.

These tests verify actual functionality, not dummy stubs.
"""

import asyncio
import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock

os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")


class TestToolSystem:
    """Test the tool system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from smith_ai.tools import ToolRegistry
        ToolRegistry._instance = None
        from smith_ai.tools import register_builtin_tools
        register_builtin_tools()
    
    def test_tools_registered(self):
        from smith_ai.tools import list_tools
        tools = list_tools()
        assert len(tools) > 0
        assert "calculator" in tools
    
    def test_get_tool(self):
        from smith_ai.tools import get_tool
        calc = get_tool("calculator")
        assert calc is not None
        assert calc.name == "calculator"
    
    @pytest.mark.asyncio
    async def test_calculator(self):
        from smith_ai.tools import CalculatorTool
        calc = CalculatorTool()
        result = await calc.execute("2 + 2")
        assert result.success
        assert result.output == "4"
    
    @pytest.mark.asyncio
    async def test_calculator_complex(self):
        from smith_ai.tools import CalculatorTool
        calc = CalculatorTool()
        result = await calc.execute("(10 + 5) * 2 - 8 / 2")
        assert result.success
        assert result.output == "26.0"
    
    @pytest.mark.asyncio
    async def test_calculator_errors(self):
        from smith_ai.tools import CalculatorTool
        calc = CalculatorTool()
        result = await calc.execute("invalid + syntax")
        assert not result.success
        assert "Error" in str(result)
    
    @pytest.mark.asyncio
    async def test_json_parse(self):
        from smith_ai.tools import JSONTool
        json_tool = JSONTool()
        result = await json_tool.execute('{"key": "value"}', "parse")
        assert result.success
    
    @pytest.mark.asyncio
    async def test_json_validate_valid(self):
        from smith_ai.tools import JSONTool
        json_tool = JSONTool()
        result = await json_tool.execute('{"valid": true}', "validate")
        assert result.success
        assert "Valid" in result.output
    
    @pytest.mark.asyncio
    async def test_json_validate_invalid(self):
        from smith_ai.tools import JSONTool
        json_tool = JSONTool()
        result = await json_tool.execute('not json', "validate")
        assert not result.success


class TestLLMSystem:
    """Test the LLM system."""
    
    def test_list_providers(self):
        from smith_ai.llm import LLMRegistry, LLMProvider
        providers = LLMRegistry.list_providers()
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.ANTHROPIC in providers
    
    def test_create_llm_openai(self):
        from smith_ai.llm import create_llm
        llm = create_llm("openai", model="gpt-4o-mini")
        assert llm is not None
        assert llm.config.model == "gpt-4o-mini"
    
    def test_create_llm_anthropic(self):
        from smith_ai.llm import create_llm
        llm = create_llm("anthropic", model="claude-3-5-sonnet")
        assert llm is not None
    
    def test_create_llm_google(self):
        from smith_ai.llm import create_llm
        llm = create_llm("google", model="gemini-2.0-flash-exp")
        assert llm is not None
    
    def test_create_llm_nvidia(self):
        from smith_ai.llm import create_llm
        llm = create_llm("nvidia", model="nvidia/nemotron-3-ultra-405b")
        assert llm is not None


class TestAgentSystem:
    """Test the agent system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from smith_ai.tools import ToolRegistry
        ToolRegistry._instance = None
        from smith_ai.tools import register_builtin_tools
        register_builtin_tools()
    
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        from smith_ai.agents import Agent
        from smith_ai.tools import get_tool
        
        calc = get_tool("calculator")
        agent = Agent(
            name="TestAgent",
            role="tester",
            goal="Test the agent system",
            llm=None,
            tools=[calc],
        )
        
        assert agent.name == "TestAgent"
        assert len(agent.tools) == 1
    
    @pytest.mark.asyncio
    async def test_agent_reset(self):
        from smith_ai.agents import Agent
        
        agent = Agent(
            name="TestAgent",
            role="tester",
            goal="Test reset",
            llm=None,
            tools=[],
        )
        
        agent.messages.append({"role": "user", "content": "test"})
        assert len(agent.messages) > 1
        
        await agent.reset()
        assert len(agent.messages) == 1
    
    @pytest.mark.asyncio
    async def test_agent_add_tool(self):
        from smith_ai.agents import Agent
        from smith_ai.tools import CalculatorTool
        
        agent = Agent(name="Test", role="t", goal="g", llm=None, tools=[])
        assert len(agent.tools) == 0
        
        agent.add_tool(CalculatorTool())
        assert len(agent.tools) == 1


class TestCrewSystem:
    """Test the crew system."""
    
    def test_create_crew(self):
        from smith_ai.agents import Agent, Task, Crew, Process
        
        agent1 = Agent(name="Agent1", role="role1", goal="goal1", llm=None)
        agent2 = Agent(name="Agent2", role="role2", goal="goal2", llm=None)
        
        task1 = Task(description="Task 1", agent_name="agent1")
        task2 = Task(description="Task 2", agent_name="agent2")
        
        crew = Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.SEQUENTIAL,
        )
        
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
        assert crew.process == Process.SEQUENTIAL
    
    def test_crew_parallel(self):
        from smith_ai.agents import Agent, Task, Crew, Process
        
        agent1 = Agent(name="Agent1", role="role1", goal="goal1", llm=None)
        task1 = Task(description="Task 1", agent_name="agent1")
        
        crew = Crew(
            agents=[agent1],
            tasks=[task1],
            process=Process.PARALLEL,
        )
        
        assert crew.process == Process.PARALLEL


class TestMemory:
    """Test the memory system."""
    
    @pytest.mark.asyncio
    async def test_document_creation(self):
        from smith_ai.memory import Document
        
        doc = Document.from_text("Test content", {"key": "value"})
        assert doc.content == "Test content"
        assert doc.metadata["key"] == "value"
        assert doc.id is not None
    
    @pytest.mark.asyncio
    async def test_cosine_similarity(self):
        from smith_ai.memory import cosine_similarity
        
        sim = cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert sim == 1.0
        
        sim = cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert sim == 0.0
    
    @pytest.mark.asyncio
    async def test_knowledge_graph(self):
        from smith_ai.memory import KnowledgeGraph
        
        kg = KnowledgeGraph()
        kg.add_node("A", {"name": "Node A"})
        kg.add_node("B", {"name": "Node B"})
        kg.add_edge("A", "B", "connects_to")
        
        neighbors = kg.get_neighbors("A")
        assert len(neighbors) == 1
        assert neighbors[0][0] == "B"


class TestEnterprise:
    """Test enterprise features."""
    
    def test_rate_limiter_creation(self):
        from smith_ai.enterprise import RateLimiter, RateLimitConfig
        
        config = RateLimitConfig(requests_per_minute=60)
        limiter = RateLimiter(config)
        
        assert limiter.config.requests_per_minute == 60
    
    @pytest.mark.asyncio
    async def test_token_bucket(self):
        from smith_ai.enterprise import TokenBucket
        
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        
        assert await bucket.acquire(3)
        assert await bucket.acquire(2)
        assert not await bucket.acquire(1)
    
    def test_circuit_breaker_creation(self):
        from smith_ai.enterprise import CircuitBreaker, CircuitBreakerConfig, CircuitState
        
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitState.CLOSED
    
    def test_memory_cache(self):
        from smith_ai.enterprise import MemoryCache
        
        cache = MemoryCache()
        
        asyncio.run(cache.set("key1", "value1"))
        value = asyncio.run(cache.get("key1"))
        assert value == "value1"
        
        exists = asyncio.run(cache.exists("key1"))
        assert exists
        
        asyncio.run(cache.delete("key1"))
        value = asyncio.run(cache.get("key1"))
        assert value is None
    
    def test_secrets_manager(self):
        from smith_ai.enterprise import SecretsManager
        
        secrets = SecretsManager()
        secrets.set("api_key", "secret123")
        
        assert secrets.get("api_key") == "secret123"
        assert secrets.get("missing") is None
        assert secrets.get("missing", "default") == "default"
        
        assert secrets.mask("very-secret-value") == "very***alue"
    
    def test_observability(self):
        from smith_ai.enterprise import Observability
        
        obs = Observability()
        
        obs.trace("test_op", "test_agent", duration_ms=100)
        obs.log("info", "Test message", agent="test")
        
        traces = obs.get_traces()
        assert len(traces) == 1
        
        logs = obs.get_logs()
        assert len(logs) == 1
        
        metrics = obs.get_metrics()
        assert "test_agent.test_op" in metrics


class TestStorage:
    """Test storage backends."""
    
    def test_postgres_config(self):
        from smith_ai.storage import DatabaseConfig
        config = DatabaseConfig(host="localhost", database="test")
        assert config.host == "localhost"
        assert config.database == "test"
    
    def test_redis_config(self):
        from smith_ai.storage import RedisConfig
        config = RedisConfig(host="localhost", port=6379)
        assert config.host == "localhost"
        assert config.port == 6379
    
    def test_mongo_config(self):
        from smith_ai.storage import MongoConfig
        config = MongoConfig(host="localhost", database="test")
        assert config.host == "localhost"
    
    def test_redis_config(self):
        from smith_ai.storage import RedisConfig
        
        config = RedisConfig(host="localhost", port=6379)
        assert config.host == "localhost"
        assert config.port == 6379


class TestEdge:
    """Test edge AI features."""
    
    def test_ollama_config(self):
        from smith_ai.edge import OllamaConfig, ModelSize, ModelInfo
        
        config = OllamaConfig(model="llama3.2", base_url="http://localhost:11434")
        assert config.model == "llama3.2"
        assert config.base_url == "http://localhost:11434"
    
    def test_local_model_factory(self):
        from smith_ai.edge import LocalModelFactory
        
        models = LocalModelFactory.recommended_models()
        assert len(models) > 0
        
        assert models[0].name.startswith("llama")


class TestDecorators:
    """Test decorators."""
    
    @pytest.mark.asyncio
    async def test_tool_decorator(self):
        from smith_ai.tools import tool, get_tool, ToolRegistry
        
        @tool(name="test_decorated", description="A test tool")
        async def test_func(x: int, y: int) -> str:
            return str(x + y)
        
        registry = ToolRegistry.get_instance()
        registry.register(test_func)
        
        tool_instance = get_tool("test_decorated")
        assert tool_instance is not None
        
        result = await tool_instance.execute(x=5, y=3)
        assert result.success
        assert result.output == "8"
    
    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        from smith_ai.enterprise import retry, RetryConfig
        
        attempt_count = 0
        
        async def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Not ready yet")
            return "Success"
        
        config = RetryConfig(max_attempts=5, initial_delay=0.01)
        result = await retry(flaky_function, config)
        
        assert result == "Success"
        assert attempt_count == 3


class TestSandbox:
    """Test sandbox system."""
    
    @pytest.mark.asyncio
    async def test_sandbox_exec(self):
        from smith_ai.sandbox import Sandbox
        
        sandbox = Sandbox()
        result = await sandbox.exec_async("echo 'hello from sandbox'")
        
        assert "hello from sandbox" in result.get("stdout", "")
        assert result.get("returncode") == 0
    
    @pytest.mark.asyncio
    async def test_sandbox_tool(self):
        from smith_ai.sandbox import SandboxTool
        
        tool = SandboxTool()
        result = await tool.execute("echo test", language="shell")
        
        assert "test" in result.output


class TestRuntime:
    """Test runtime system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        from smith_ai.tools import ToolRegistry
        ToolRegistry._instance = None
        from smith_ai.tools import register_builtin_tools
        register_builtin_tools()
    
    @pytest.mark.asyncio
    async def test_runtime_initialization(self):
        from smith_ai.runtime import Runtime, RuntimeConfig
        
        runtime = Runtime()
        await runtime.initialize()
        
        assert runtime._initialized
    
    @pytest.mark.asyncio
    async def test_runtime_status(self):
        from smith_ai.runtime import Runtime, RuntimeConfig
        
        runtime = Runtime()
        await runtime.initialize()
        
        status = runtime.status()
        assert "initialized" in status
        assert status["initialized"]


class TestCrewOrchestration:
    """Test crew orchestration."""
    
    def test_task_to_dict(self):
        from smith_ai.agents import Task
        
        task = Task(
            description="Test task",
            agent_name="TestAgent",
            expected_output="Expected result"
        )
        
        d = task.to_dict()
        assert d["description"] == "Test task"
        assert d["agent_name"] == "TestAgent"


def run_tests():
    """Run all tests with coverage."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
