"""Comprehensive tests for SmithAI framework."""

import asyncio
import pytest

from smith_ai import (
    Agent,
    Task,
    Crew,
    Process,
    create_llm,
    list_tools,
    get_tool,
    register_builtin_tools,
    CalculatorTool,
    WebSearchTool,
    PythonREPLTool,
    JSONTool,
    Runtime,
    RuntimeConfig,
    Sandbox,
    SandboxTool,
    LLMProvider,
    LLMRegistry,
    ToolRegistry,
)


class TestToolSystem:
    """Test the tool system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        register_builtin_tools()
    
    def test_tools_registered(self):
        tools = list_tools()
        assert len(tools) > 0
        assert "calculator" in tools
        assert "web_search" in tools
        assert "python_repl" in tools
    
    def test_get_tool(self):
        calc = get_tool("calculator")
        assert calc is not None
        assert calc.name == "calculator"
    
    @pytest.mark.asyncio
    async def test_calculator(self):
        calc = CalculatorTool()
        result = await calc.execute("2 + 2")
        assert result.success
        assert result.output == "4"
    
    @pytest.mark.asyncio
    async def test_calculator_errors(self):
        calc = CalculatorTool()
        result = await calc.execute("invalid + syntax")
        assert not result.success
        assert "Error" in str(result)
    
    @pytest.mark.asyncio
    async def test_json_tool(self):
        json_tool = JSONTool()
        result = await json_tool.execute('{"key": "value"}', "parse")
        assert result.success
    
    @pytest.mark.asyncio
    async def test_json_validate(self):
        json_tool = JSONTool()
        result = await json_tool.execute('{"valid": true}', "validate")
        assert result.success
        assert "Valid" in result.output
    
    @pytest.mark.asyncio
    async def test_json_invalid(self):
        json_tool = JSONTool()
        result = await json_tool.execute('not json', "validate")
        assert not result.success


class TestLLMSystem:
    """Test the LLM system."""
    
    def test_list_providers(self):
        providers = LLMRegistry.list_providers()
        assert LLMProvider.OPENAI in providers
        assert LLMProvider.ANTHROPIC in providers
        assert LLMProvider.GOOGLE in providers
        assert LLMProvider.NVIDIA in providers
    
    def test_create_llm_openai(self):
        llm = create_llm("openai", model="gpt-4o-mini")
        assert llm is not None
    
    def test_create_llm_anthropic(self):
        llm = create_llm("anthropic", model="claude-3-5-sonnet")
        assert llm is not None
    
    def test_create_llm_google(self):
        llm = create_llm("google", model="gemini-2.0-flash-exp")
        assert llm is not None
    
    def test_create_llm_nvidia(self):
        llm = create_llm("nvidia", model="nvidia/nemotron-3-ultra-405b")
        assert llm is not None


class TestAgentSystem:
    """Test the agent system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        register_builtin_tools()
    
    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        calc = get_tool("calculator")
        agent = Agent(
            name="TestAgent",
            role="tester",
            goal="Test the agent system",
            llm=None,  # No LLM, just testing tool execution
            tools=[calc],
        )
        
        # Just verify agent is created correctly
        assert agent.name == "TestAgent"
        assert len(agent.tools) == 1
    
    @pytest.mark.asyncio
    async def test_agent_reset(self):
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
        assert len(agent.messages) == 1  # Only system prompt


class TestCrewSystem:
    """Test the crew system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        register_builtin_tools()
    
    def test_create_crew(self):
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
    
    def test_crew_parallel_process(self):
        agent1 = Agent(name="Agent1", role="role1", goal="goal1", llm=None)
        task1 = Task(description="Task 1", agent_name="agent1")
        
        crew = Crew(
            agents=[agent1],
            tasks=[task1],
            process=Process.PARALLEL,
        )
        
        assert crew.process == Process.PARALLEL


class TestRuntime:
    """Test the runtime system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        register_builtin_tools()
    
    @pytest.mark.asyncio
    async def test_runtime_initialization(self):
        runtime = Runtime()
        await runtime.initialize()
        
        assert runtime._initialized
        assert len(ToolRegistry.get_instance().list_all()) > 0
    
    @pytest.mark.asyncio
    async def test_runtime_status(self):
        runtime = Runtime()
        await runtime.initialize()
        
        status = runtime.status()
        assert "initialized" in status
        assert "tools" in status
        assert status["initialized"]
    
    @pytest.mark.asyncio
    async def test_runtime_tools(self):
        runtime = Runtime(RuntimeConfig(auto_register_tools=True))
        await runtime.initialize()
        
        tools = runtime.list_tools()
        assert len(tools) > 0


class TestSandbox:
    """Test the sandbox system."""
    
    @pytest.mark.asyncio
    async def test_sandbox_exec(self):
        sandbox = Sandbox()
        result = await sandbox.exec_async("echo 'hello'")
        
        assert "hello" in result.get("stdout", "")
    
    @pytest.mark.asyncio
    async def test_sandbox_tool(self):
        tool = SandboxTool()
        result = await tool.execute("echo test", language="shell")
        
        assert "test" in result.output


class TestDecorators:
    """Test the @tool decorator."""
    
    @pytest.mark.asyncio
    async def test_tool_decorator(self):
        from smith_ai.tools import tool, get_tool, ToolRegistry
        
        @tool(name="test_decorated", description="A test tool")
        async def test_func(x: int, y: int) -> str:
            return str(x + y)
        
        # Register and test
        registry = ToolRegistry.get_instance()
        registry.register(test_func)
        
        tool_instance = get_tool("test_decorated")
        assert tool_instance is not None
        
        result = await tool_instance.execute(x=5, y=3)
        assert result.success
        assert result.output == "8"


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
