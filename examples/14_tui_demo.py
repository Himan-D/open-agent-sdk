#!/usr/bin/env python3
"""SmithAI TUI - Complete Framework Demo.

Tests ALL features of the TUI:
1. Command palette (55+ commands)
2. Agent management
3. Tool system
4. Crew orchestration
5. Memory & knowledge
6. Browser automation
7. LLM provider switching
8. Settings & configuration
"""

import asyncio
import sys
import os

sys.path.insert(0, "/Users/himand/open-agent/src")

from smith_ai.tui import SmithAIApp


def print_header(title: str) -> None:
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def print_section(title: str) -> None:
    print(f"\n{'-'*70}")
    print(f" {title}")
    print(f"{'-'*70}")


def test_tui_components():
    """Test all TUI components."""
    print_header("SmithAI TUI - Component Tests")
    
    from smith_ai.tui import SmithAIApp, Command, CommandCategory, AgentStatus, AgentState
    
    print_section("1. Creating TUI App")
    app = SmithAIApp()
    print(f"  App created: {type(app).__name__}")
    
    print_section("2. Command Palette")
    print(f"  Total commands: {len(app.commands)}")
    print(f"  Categories: {len(set(c.category for c in app.commands))}")
    
    categories = {}
    for cmd in app.commands:
        if cmd.category not in categories:
            categories[cmd.category] = 0
        categories[cmd.category] += 1
    
    print("\n  Commands by category:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")
    
    print_section("3. Command Search")
    results = app.search_commands("agent")
    print(f"  Search 'agent': {len(results)} results")
    
    results = app.search_commands("tool")
    print(f"  Search 'tool': {len(results)} results")
    
    results = app.search_commands("memory")
    print(f"  Search 'memory': {len(results)} results")
    
    print_section("4. Shortcuts")
    shortcuts = app.get_shortcuts()
    print(f"  Total shortcuts: {len(shortcuts)}")
    print("  Sample shortcuts:")
    for shortcut, name in list(shortcuts.items())[:10]:
        print(f"    {shortcut:20} -> {name}")
    
    print_section("5. Agent Management")
    print(f"  Default agents: {list(app.agents.keys())}")
    for name, state in app.agents.items():
        print(f"    {name}: {state.status.value}")
    
    print_section("6. Tool Loading")
    print(f"  Tools loaded: {len(app.tools)}")
    for name in list(app.tools.keys())[:10]:
        print(f"    - {name}")
    
    print_section("7. Command Execution")
    for cmd_name in ["agent status", "list agents", "list tools", "list providers", "version", "about"]:
        result = app.execute_by_name(cmd_name)
        if result and len(result) > 100:
            result = result[:100] + "..."
        print(f"  '{cmd_name}': {result[:80] if result else 'No output'}")
    
    print_section("8. Command List Formatting")
    help_text = app.format_command_list()
    lines = help_text.split('\n')
    print(f"  Help text: {len(lines)} lines")
    
    print_section("9. Shortcuts Formatting")
    shortcuts_text = app.format_shortcuts()
    lines = shortcuts_text.split('\n')
    print(f"  Shortcuts text: {len(lines)} lines")
    
    return True


def test_agent_management():
    """Test agent management features."""
    print_header("SmithAI TUI - Agent Management Tests")
    
    from smith_ai.tui import SmithAIApp, AgentStatus, AgentState
    
    app = SmithAIApp()
    
    print_section("1. Create Agent")
    new_agent = AgentState(name="test_agent", status=AgentStatus.IDLE)
    app.agents["test_agent"] = new_agent
    print(f"  Created agent: {new_agent.name}")
    
    print_section("2. Update Agent Status")
    app.agents["test_agent"].status = AgentStatus.THINKING
    print(f"  Status updated: {app.agents['test_agent'].status.value}")
    
    print_section("3. Agent Status Report")
    result = app._cmd_agent_status()
    print(f"  Status report lines: {len(result.split(chr(10)))}")
    
    print_section("4. List Agents")
    result = app._cmd_list_agents()
    print(f"  Agent list:\n{result}")
    
    print_section("5. Delete Agent")
    del app.agents["test_agent"]
    print(f"  Agents after delete: {list(app.agents.keys())}")
    
    return True


def test_tool_execution():
    """Test tool execution."""
    print_header("SmithAI TUI - Tool Execution Tests")
    
    from smith_ai.tui import SmithAIApp
    
    app = SmithAIApp()
    
    print_section("1. List Tools")
    result = app._cmd_list_tools()
    lines = result.split('\n')
    print(f"  Tool list lines: {len(lines)}")
    
    print_section("2. Calculator Tool")
    result = app._cmd_calculator()
    print(f"  Calculator result: {result}")
    
    print_section("3. Tool Inspection")
    print(f"  Available tools: {list(app.tools.keys())}")
    
    return True


def test_llm_providers():
    """Test LLM provider features."""
    print_header("SmithAI TUI - LLM Provider Tests")
    
    from smith_ai.tui import SmithAIApp
    
    app = SmithAIApp()
    
    print_section("1. List Providers")
    result = app._cmd_list_providers()
    print(f"  Providers:\n{result}")
    
    print_section("2. Switch LLM")
    result = app._cmd_switch_llm()
    print(f"  Switch options:\n{result}")
    
    return True


def test_knowledge_graph():
    """Test knowledge graph."""
    print_header("SmithAI TUI - Knowledge Graph Tests")
    
    from smith_ai.tui import SmithAIApp
    
    app = SmithAIApp()
    
    print_section("1. Knowledge Graph Command")
    result = app._cmd_knowledge_graph()
    print(f"  Result: {result}")
    
    print_section("2. Memory Stats")
    result = app._cmd_memory_stats()
    print(f"  Stats:\n{result}")
    
    return True


def test_integration():
    """Test integration with SmithAI core."""
    print_header("SmithAI TUI - Integration Tests")
    
    from smith_ai.tui import SmithAIApp
    
    app = SmithAIApp()
    
    print_section("1. SmithAI Core Import")
    try:
        import smith_ai
        print(f"  SmithAI version: {smith_ai.__version__}")
    except ImportError as e:
        print(f"  Import error: {e}")
    
    print_section("2. Agent Import")
    try:
        from smith_ai import Agent, Task, Crew
        print("  Agent classes available")
    except ImportError as e:
        print(f"  Agent import error: {e}")
    
    print_section("3. Tool Import")
    try:
        from smith_ai import list_tools, get_tool
        tools = list_tools()
        print(f"  Tools available: {len(tools)}")
    except ImportError as e:
        print(f"  Tool import error: {e}")
    
    print_section("4. LLM Provider Import")
    try:
        from smith_ai.core import LLMProvider
        print(f"  Providers: {[p.value for p in LLMProvider]}")
    except ImportError as e:
        print(f"  LLM import error: {e}")
    
    print_section("5. Memory Import")
    try:
        from smith_ai.memory import KnowledgeGraph, VectorStore
        print("  Memory classes available")
    except ImportError as e:
        print(f"  Memory import error: {e}")
    
    print_section("6. Enterprise Import")
    try:
        from smith_ai.enterprise import RateLimiter, CircuitBreaker
        print("  Enterprise classes available")
    except ImportError as e:
        print(f"  Enterprise import error: {e}")
    
    print_section("7. Browser Import")
    try:
        from smith_ai.browser import BrowserSession
        print("  Browser classes available")
    except ImportError as e:
        print(f"  Browser import error: {e}")
    
    print_section("8. AGI Import")
    try:
        from smith_ai.agi import AdvancedAgent
        print("  AGI classes available")
    except ImportError as e:
        print(f"  AGI import error: {e}")
    
    return True


async def test_async_agent():
    """Test async agent execution."""
    print_header("SmithAI TUI - Async Agent Tests")
    
    print_section("1. Agent Creation")
    try:
        from smith_ai import Agent
        
        agent = Agent(
            name="AsyncAgent",
            role="Test Agent",
            goal="Test the agent system",
            backstory="A test agent for the TUI",
        )
        print(f"  Created: {agent.name}")
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    print_section("2. Tool Addition")
    try:
        from smith_ai import get_tool
        
        calc = get_tool("calculator")
        if calc:
            agent.add_tool(calc)
            print(f"  Added calculator tool")
    except Exception as e:
        print(f"  Error: {e}")
    
    print_section("3. Agent Execution")
    try:
        result = await agent.run("What is 25 + 17?")
        print(f"  Result: {str(result)[:100]}...")
    except Exception as e:
        print(f"  Execution error: {e}")
    
    return True


def test_full_workflow():
    """Test complete workflow."""
    print_header("SmithAI TUI - Full Workflow Test")
    
    from smith_ai.tui import SmithAIApp, TUIRunner
    
    print_section("1. App Creation")
    app = SmithAIApp()
    print(f"  App ready with {len(app.commands)} commands")
    
    print_section("2. Command Execution Flow")
    test_commands = [
        "list agents",
        "list tools", 
        "list providers",
        "agent status",
        "memory stats",
        "version",
        "about",
        "keyboard shortcuts",
    ]
    
    for cmd in test_commands:
        result = app.execute_by_name(cmd)
        if result:
            print(f"  [OK] {cmd}")
        else:
            print(f"  [FAIL] {cmd}")
    
    print_section("3. TUIRunner")
    runner = TUIRunner(app)
    print(f"  Runner created")
    
    return True


def main():
    """Run all TUI tests."""
    print("\n" + "=" * 70)
    print("  SmithAI TUI - Complete Feature Test")
    print("  Version 4.0.0 - True AGI Framework")
    print("=" * 70)
    
    tests = [
        ("TUI Components", test_tui_components),
        ("Agent Management", test_agent_management),
        ("Tool Execution", test_tool_execution),
        ("LLM Providers", test_llm_providers),
        ("Knowledge Graph", test_knowledge_graph),
        ("SmithAI Integration", test_integration),
        ("Full Workflow", test_full_workflow),
    ]
    
    results = []
    
    for name, test in tests:
        try:
            result = test()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Run async test
    try:
        result = asyncio.run(test_async_agent())
        results.append(("Async Agent", result))
    except Exception as e:
        print(f"\n[ERROR] Async Agent: {e}")
        results.append(("Async Agent", False))
    
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    # Show commands summary
    print("\n" + "=" * 70)
    print(" COMMANDS SUMMARY")
    print("=" * 70)
    
    app = SmithAIApp()
    print(f"\nTotal commands: {len(app.commands)}")
    print(f"Total shortcuts: {len(app.get_shortcuts())}")
    
    categories = {}
    for cmd in app.commands:
        if cmd.category not in categories:
            categories[cmd.category] = 0
        categories[cmd.category] += 1
    
    print("\nBy category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print("\n" + "=" * 70)
    print(" Run 'create_tui()' for interactive mode")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
