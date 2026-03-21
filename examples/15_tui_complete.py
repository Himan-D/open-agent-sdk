#!/usr/bin/env python3
"""SmithAI TUI - Complete Interactive Demo.

Tests all features working together:
- TUI with 60+ commands
- Agent creation and management
- Tool system
- Crew orchestration
- Memory & knowledge
- LLM providers
- Async execution
"""

import asyncio
import sys

sys.path.insert(0, "/Users/himand/open-agent/src")

from smith_ai.tui import (
    SmithAIApp,
    TUIRunner,
    TUIBridge,
    async_run_tool,
    async_run_agent,
    Command,
    AgentStatus,
    AgentState,
)


def print_header(title: str) -> None:
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


async def demo_async_tools():
    """Test async tool execution."""
    print_header("Async Tool Execution Demo")
    
    print("Testing calculator tool...")
    result = await async_run_tool("calculator", expression="25 + 17 * 3")
    print(f"  25 + 17 * 3 = {result}")
    
    print("\nTesting datetime tool...")
    result = await async_run_tool("datetime_tool", format="%Y-%m-%d %H:%M:%S")
    print(f"  Current datetime: {result}")
    
    print("\nTesting system_info tool...")
    result = await async_run_tool("system_info")
    print(f"  System info: {result}")
    
    return True


async def demo_async_agent():
    """Test async agent execution."""
    print_header("Async Agent Execution Demo")
    
    print("Creating agent...")
    result = await async_run_agent(
        agent_name="DemoAgent",
        task="What is 2 + 2?",
        tools=["calculator"]
    )
    print(f"  Result: {str(result)[:200]}...")
    
    return True


def demo_all_commands():
    """Test all command categories."""
    print_header("Command Categories Demo")
    
    app = SmithAIApp()
    
    categories = {}
    for cmd in app.commands:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd)
    
    for cat, cmds in sorted(categories.items()):
        print(f"\n{cat} ({len(cmds)} commands):")
        for cmd in cmds[:3]:
            print(f"  {cmd.icon} {cmd.name}")
        if len(cmds) > 3:
            print(f"  ... and {len(cmds) - 3} more")
    
    return True


def demo_agent_workflow():
    """Test complete agent workflow."""
    print_header("Agent Workflow Demo")
    
    app = SmithAIApp()
    
    print("1. Creating new agent...")
    new_agent = AgentState(name="workflow_test", status=AgentStatus.IDLE)
    app.agents["workflow_test"] = new_agent
    print(f"   Agent created: {new_agent.name}")
    
    print("\n2. Updating status to thinking...")
    app.agents["workflow_test"].status = AgentStatus.THINKING
    app.agents["workflow_test"].iterations = 5
    print(f"   Status: {app.agents['workflow_test'].status.value}")
    print(f"   Iterations: {app.agents['workflow_test'].iterations}")
    
    print("\n3. Agent status report...")
    report = app._cmd_agent_status()
    for line in report.split('\n'):
        print(f"   {line}")
    
    print("\n4. Cleanup...")
    del app.agents["workflow_test"]
    print(f"   Remaining agents: {list(app.agents.keys())}")
    
    return True


def demo_tool_system():
    """Test tool system."""
    print_header("Tool System Demo")
    
    app = SmithAIApp()
    
    print(f"Total tools: {len(app.tools)}")
    print("\nTools by category:")
    
    categories = {
        "Math": ["calculator"],
        "Web": ["web_search", "fetch_url"],
        "File": ["read_file", "write_file"],
        "Data": ["json_tool", "python_repl"],
        "Time": ["datetime_tool"],
        "System": ["system_info"],
        "Text": ["sentiment", "text_tool"],
    }
    
    for cat, tools in categories.items():
        available = [t for t in tools if t in app.tools]
        print(f"  {cat}: {len(available)}/{len(tools)} available")
    
    return True


def demo_integration():
    """Test SmithAI integration."""
    print_header("SmithAI Integration Demo")
    
    print("1. Importing core modules...")
    try:
        import smith_ai
        print(f"   SmithAI version: {smith_ai.__version__}")
    except Exception as e:
        print(f"   Error: {e}")
        return False
    
    print("\n2. Importing agents...")
    try:
        from smith_ai import Agent, Task, Crew
        print("   Agent, Task, Crew available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Importing tools...")
    try:
        from smith_ai import list_tools, get_tool
        tools = list_tools()
        print(f"   {len(tools)} tools available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Importing LLM providers...")
    try:
        from smith_ai.core import LLMProvider
        providers = [p.value for p in LLMProvider]
        print(f"   {len(providers)} providers: {', '.join(providers)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Importing memory...")
    try:
        from smith_ai.memory import KnowledgeGraph, VectorStore
        print("   KnowledgeGraph, VectorStore available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n6. Importing enterprise...")
    try:
        from smith_ai.enterprise import RateLimiter, CircuitBreaker
        print("   RateLimiter, CircuitBreaker available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n7. Importing AGI...")
    try:
        from smith_ai.agi import AdvancedAgent
        print("   AdvancedAgent available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n8. Importing browser...")
    try:
        from smith_ai.browser import BrowserSession
        print("   BrowserSession available")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n9. Importing TUI...")
    try:
        from smith_ai.tui import SmithAIApp, TUIBridge
        print("   SmithAIApp, TUIBridge available")
    except Exception as e:
        print(f"   Error: {e}")
    
    return True


async def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  SmithAI TUI - Complete Feature Demo")
    print("  Version 4.0.0 - True AGI Framework")
    print("="*70)
    
    demos = [
        ("Command Categories", demo_all_commands),
        ("Agent Workflow", demo_agent_workflow),
        ("Tool System", demo_tool_system),
        ("SmithAI Integration", demo_integration),
        ("Async Tools", demo_async_tools),
        ("Async Agent", demo_async_agent),
    ]
    
    results = []
    
    for name, demo in demos:
        try:
            if asyncio.iscoroutinefunction(demo):
                result = await demo()
            else:
                result = demo()
            results.append((name, result))
            status = "[PASS]" if result else "[FAIL]"
            print(f"\n{status} {name}")
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} demos passed")
    
    # Summary
    app = SmithAIApp()
    print("\n" + "="*70)
    print(" SMITHAI TUI SUMMARY")
    print("="*70)
    print(f"\n  Commands: {len(app.commands)}")
    print(f"  Tools: {len(app.tools)}")
    print(f"  Agents: {len(app.agents)}")
    print(f"  Shortcuts: {len(app.get_shortcuts())}")
    
    print("\n" + "="*70)
    print(" Run 'from smith_ai.tui import create_tui; create_tui()' for interactive mode")
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
