#!/usr/bin/env python3
"""SmithAI Demo - Production AI Agent Framework.

This demo shows how to use SmithAI:
1. Tool System
2. Multi-LLM Support
3. Agent Creation
4. Crew Orchestration
"""

import asyncio
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-demo")

from smith_ai import (
    Agent, Task, Crew, Process,
    create_llm, list_tools, get_tool, register_builtin_tools,
    CalculatorTool, WebSearchTool, JSONTool,
    Runtime, RuntimeConfig,
    Sandbox,
    tool,
)


async def demo_tools():
    """Demo the tool system."""
    print("\n" + "=" * 60)
    print("DEMO 1: Tool System")
    print("=" * 60)
    
    register_builtin_tools()
    
    print(f"\nRegistered {len(list_tools())} tools:")
    for name in list_tools()[:5]:
        tool = get_tool(name)
        print(f"  - {name}: {tool.description[:50]}...")
    
    print("\nTesting Calculator:")
    calc = CalculatorTool()
    result = await calc.execute("2 + 2 * 10")
    print(f"  2 + 2 * 10 = {result.output}")
    
    print("\nTesting JSON Tool:")
    json_tool = JSONTool()
    result = await json_tool.execute('{"name": "test", "value": 42}', "parse")
    print(f"  Parsed JSON: {result.output[:50]}...")


async def demo_llm():
    """Demo the LLM system."""
    print("\n" + "=" * 60)
    print("DEMO 2: Multi-LLM Support")
    print("=" * 60)
    
    providers = ["openai", "anthropic", "google", "nvidia", "ollama", "mistral"]
    
    for provider in providers:
        try:
            llm = create_llm(provider, model="test-model")
            print(f"  [OK] {provider}")
        except Exception as e:
            print(f"  [SKIP] {provider}: {str(e)[:40]}")


async def demo_agents():
    """Demo the agent system."""
    print("\n" + "=" * 60)
    print("DEMO 3: Agent System")
    print("=" * 60)
    
    register_builtin_tools()
    calc = get_tool("calculator")
    
    agent = Agent(
        name="CalculatorBot",
        role="mathematician",
        goal="Calculate accurately",
        llm=None,  # Would need real API key
        tools=[calc],
        verbose=False,
    )
    
    print(f"\nAgent created: {agent.name}")
    print(f"Role: {agent.role}")
    print(f"Tools: {[t.name for t in agent.tools]}")
    
    await agent.reset()
    print("Agent reset successfully")


async def demo_crew():
    """Demo the crew system."""
    print("\n" + "=" * 60)
    print("DEMO 4: Crew Orchestration")
    print("=" * 60)
    
    register_builtin_tools()
    
    # Create agents
    researcher = Agent(
        name="Researcher",
        role="researcher",
        goal="Research topics thoroughly",
        llm=None,
        tools=[get_tool("calculator")],
    )
    
    writer = Agent(
        name="Writer",
        role="writer",
        goal="Write clear summaries",
        llm=None,
        tools=[],
    )
    
    # Create tasks
    task1 = Task(
        description="Research the benefits of AI agents",
        agent_name="Researcher",
        expected_output="Key findings about AI agents",
    )
    
    task2 = Task(
        description="Write a summary based on the research",
        agent_name="Writer",
        expected_output="Clear summary paragraph",
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, writer],
        tasks=[task1, task2],
        process=Process.SEQUENTIAL,
    )
    
    print(f"\nCrew created with {len(crew.agents)} agents")
    print(f"Tasks: {len(crew.tasks)}")
    print(f"Process: {crew.process.value}")


async def demo_runtime():
    """Demo the runtime system."""
    print("\n" + "=" * 60)
    print("DEMO 5: Runtime Environment")
    print("=" * 60)
    
    runtime = Runtime(RuntimeConfig(auto_register_tools=True))
    await runtime.initialize()
    
    status = runtime.status()
    print(f"\nRuntime initialized: {status['initialized']}")
    print(f"Tools available: {status['tools']}")
    
    # Register a custom agent
    agent = Agent(name="TestAgent", role="tester", goal="Test", llm=None)
    runtime.register_agent(agent)
    
    print(f"Agents registered: {runtime.list_agents()}")


async def demo_decorator():
    """Demo the @tool decorator."""
    print("\n" + "=" * 60)
    print("DEMO 6: @tool Decorator")
    print("=" * 60)
    
    from smith_ai.tools import register_tool, get_tool
    
    @tool(name="greet", description="Greet someone by name")
    async def greet(name: str) -> str:
        return f"Hello, {name}! Welcome to SmithAI."
    
    register_tool(greet)
    
    print("\nCreated custom 'greet' tool:")
    print(f"  Name: {greet.name}")
    print(f"  Description: {greet.description}")
    
    result = await greet.execute(name="User")
    print(f"  Result: {result.output}")


async def demo_sandbox():
    """Demo the sandbox system."""
    print("\n" + "=" * 60)
    print("DEMO 7: Sandbox Execution")
    print("=" * 60)
    
    sandbox = Sandbox()
    
    print("\nExecuting in sandbox:")
    result = await sandbox.exec_async("echo 'Hello from sandbox!'")
    print(f"  Output: {result.get('stdout', '').strip()}")
    
    print("\nExecuting Python in sandbox:")
    result = await sandbox.exec_python_async("print('Python works in sandbox!')")
    print(f"  Output: {result.get('stdout', '').strip()}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("SmithAI - Production AI Agent Framework")
    print("=" * 60)
    
    await demo_tools()
    await demo_llm()
    await demo_agents()
    await demo_crew()
    await demo_runtime()
    await demo_decorator()
    await demo_sandbox()
    
    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
    print("\nTo use SmithAI with real LLMs:")
    print("  1. Set environment variables:")
    print("     export OPENAI_API_KEY='your-key'")
    print("     export ANTHROPIC_API_KEY='your-key'")
    print("     export NVIDIA_API_KEY='your-key'")
    print("  2. Create agents with tools:")
    print("     agent = create_agent('assistant', 'helpful', 'assist users')")
    print("  3. Run tasks:")
    print("     result = await agent.run('What is 2+2?')")
    print()


if __name__ == "__main__":
    asyncio.run(main())
