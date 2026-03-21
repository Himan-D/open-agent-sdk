#!/usr/bin/env python3
"""
🚀 SmithAI - UNIFIED ORCHESTRATION DEMO

This demonstrates the unified framework that combines everything:
1. DeepAgent - Core AI agent
2. OpenClaw - Multi-agent with SOUL.md
3. OpenShell - Sandbox execution
4. All Tools - Browser, Calculator, Code, etc.

Run: python examples/08_unified_demo.py
"""

import asyncio
import os

# Get API key from environment (set NVIDIA_API_KEY in your shell)

from open_agent import (
    # Core
    UnifiedOrchestrator, orchestrate, create_orchestrator,
    Agent, AgentConfig, Crew, Task,
    LLMFactory, LLMProvider, get_config,
    ToolRegistry,
    
    # OpenClaw
    OpenClawAgent, OpenClawCrew, SoulConfig,
    
    # OpenShell
    OpenShellBackend,
    
    # Browser
    BrowserTool,
)


async def demo_unified():
    """Demo the unified orchestrator."""
    print("\n" + "="*70)
    print("🎯 UNIFIED ORCHESTRATOR DEMO")
    print("="*70)
    
    # Create orchestrator
    orchestrator = create_orchestrator(
        llm_provider="nvidia",
        enable_sandbox=True,
        enable_browser=True,
    )
    
    print("\n[1] Initializing orchestrator...")
    await orchestrator.initialize()
    
    print("\n[2] Status check:")
    status = orchestrator.status()
    for k, v in status.items():
        print(f"    {k}: {v}")
    
    print("\n[3] Available tools:")
    tools = orchestrator.list_tools()
    print(f"    {len(tools)} tools: {tools[:5]}...")
    
    print("\n[4] Running different task types:")
    
    # Calculator
    print("\n    [4a] Calculator...")
    r = await orchestrator.run("calculate: 100 + 200")
    print(f"        Result: {r}")
    
    # Browser
    print("\n    [4b] Browser navigation...")
    r = await orchestrator.run("navigate:https://example.com")
    print(f"        Result: {r[:60]}...")
    
    # LLM
    print("\n    [4c] LLM question...")
    r = await orchestrator.run("What is 2+2?")
    print(f"        Result: {r[:80]}...")
    
    print("\n✅ Unified orchestrator works!")


async def demo_deep_agent():
    """Demo DeepAgent."""
    print("\n" + "="*70)
    print("🤖 DEEP AGENT DEMO")
    print("="*70)
    
    config = get_config()
    llm = LLMFactory.create(LLMProvider.NVIDIA, api_key=config.nvidia_api_key)
    
    print("\n[1] Creating agent with tools...")
    agent = Agent(AgentConfig(
        name="assistant",
        role="AI Assistant",
        goal="Help users",
        backstory="You are a helpful assistant.",
        verbose=False,
        llm=llm,
    ))
    
    print("\n[2] Testing agent...")
    r = await agent.execute("What is the square root of 144?")
    print(f"    Result: {r[:100]}...")
    
    print("\n✅ DeepAgent works!")


async def demo_openclaw():
    """Demo OpenClaw."""
    print("\n" + "="*70)
    print("🦞 OPENCLAW DEMO (SOUL.md)")
    print("="*70)
    
    config = get_config()
    llm = LLMFactory.create(LLMProvider.NVIDIA, api_key=config.nvidia_api_key)
    
    print("\n[1] Creating soul config (SOUL.md)...")
    soul = SoulConfig(
        name="Research Analyst",
        emoji="🔍",
        team="AI Team",
        responsibilities=["Research", "Analyze", "Report"],
        work_style=["thorough", "accurate"],
        custom_instructions="Always cite your sources."
    )
    print(f"    Soul: {soul.name} {soul.emoji}")
    print(f"    Prompt: {soul.to_system_prompt()[:80]}...")
    
    print("\n[2] Creating OpenClaw agent...")
    agent = OpenClawAgent(
        name="researcher",
        soul=soul,
        llm=llm,
    )
    
    print("\n[3] Testing agent...")
    r = await agent.think("What are 3 benefits of AI?")
    print(f"    Result: {r[:100]}...")
    
    print("\n[4] Creating crew...")
    crew = OpenClawCrew(
        agents=[agent],
        process="sequential"
    )
    
    r = await crew.kickoff("Research Python frameworks")
    print(f"    Crew result: {len(r)} tasks")
    
    print("\n✅ OpenClaw works!")


async def demo_openshell():
    """Demo OpenShell."""
    print("\n" + "="*70)
    print("🐚 OPENSHELL DEMO (Sandbox)")
    print("="*70)
    
    print("\n[1] Creating sandbox backend...")
    sandbox = OpenShellBackend()
    print(f"    OpenShell available: {sandbox._openshell_available}")
    
    print("\n[2] Creating session...")
    session = sandbox.create_sandbox("nemotron")
    print(f"    Session: {session.session_id}")
    
    print("\n[3] Executing commands...")
    r = session.exec("echo 'Hello from sandbox!'")
    print(f"    echo: {r.get('stdout', '').strip()}")
    
    r = session.exec("python3 -c 'print(2**10)'")
    print(f"    python: {r.get('stdout', '').strip()}")
    
    print("\n[4] Cleanup...")
    session.terminate()
    print("    Session terminated")
    
    print("\n✅ OpenShell works!")


async def demo_browser():
    """Demo Browser."""
    print("\n" + "="*70)
    print("🌐 BROWSER DEMO")
    print("="*70)
    
    print("\n[1] Creating browser...")
    browser = BrowserTool()
    
    print("\n[2] Navigating...")
    r = await browser.execute("navigate:https://example.com")
    print(f"    {r.output[:60]}...")
    
    print("\n[3] Getting content...")
    r = await browser.execute("title")
    print(f"    Title: {r}")
    
    r = await browser.execute("text:h1")
    print(f"    H1: {r}")
    
    print("\n[4] Screenshot...")
    r = await browser.execute("screenshot:browser_demo.png")
    print(f"    {r}")
    
    await browser.close()
    print("\n✅ Browser works!")


async def demo_multi_agent():
    """Demo Multi-Agent Crew."""
    print("\n" + "="*70)
    print("👥 MULTI-AGENT CREW DEMO")
    print("="*70)
    
    config = get_config()
    llm = LLMFactory.create(LLMProvider.NVIDIA, api_key=config.nvidia_api_key)
    
    print("\n[1] Creating specialized agents...")
    researcher = Agent(AgentConfig(
        name="researcher", role="Researcher", goal="Research",
        backstory="Expert researcher.", verbose=False, llm=llm,
    ))
    writer = Agent(AgentConfig(
        name="writer", role="Writer", goal="Write",
        backstory="Expert writer.", verbose=False, llm=llm,
    ))
    
    print(f"    ✅ {researcher.name}, {writer.name}")
    
    print("\n[2] Creating crew...")
    crew = Crew(
        agents=[researcher, writer],
        tasks=[
            Task(description="Research AI trends", agent=researcher),
            Task(description="Write about AI", agent=writer),
        ],
        process=Crew.Process.SEQUENTIAL,
        verbose=False,
    )
    
    print("\n[3] Executing crew...")
    results = await crew.kickoff()
    print(f"    ✅ {len(results)} tasks completed")
    
    for name, result in results.items():
        print(f"    {name[:40]}...: {result[:50]}...")
    
    print("\n✅ Multi-Agent Crew works!")


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 SmithAI - UNIFIED ORCHESTRATION                        ║
║                                                              ║
║   Everything working together:                               ║
║   • DeepAgent - Core AI                                    ║
║   • OpenClaw - Multi-agent with SOUL.md                     ║
║   • OpenShell - Sandbox execution                           ║
║   • Browser - Web automation                                ║
║   • Tools - Calculator, Code, etc.                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    await demo_unified()
    await demo_deep_agent()
    await demo_openclaw()
    await demo_openshell()
    await demo_browser()
    await demo_multi_agent()
    
    print("\n" + "="*70)
    print("🎉 ALL DEMOS COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
