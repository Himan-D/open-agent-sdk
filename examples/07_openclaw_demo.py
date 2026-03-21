#!/usr/bin/env python3
"""
🚀 OpenShell & OpenClaw Integration Demo

This demonstrates full integration with:
- OpenShell: Isolated sandbox execution
- OpenClaw: Multi-agent orchestration with skills & delegation

Run: python examples/07_openclaw_demo.py
"""

import asyncio
import os

os.environ['NVIDIA_API_KEY'] = 'REDACTED_API_KEY'

from open_agent.integrations.openclawsdk import (
    OpenShellBackend, SandboxSession, SandboxType, SandboxConfig,
    OpenClawAgent, OpenClawCrew, SoulConfig, Skill,
    create_openshell_sandbox, create_openclaw_agent, create_openclaw_crew,
)
from open_agent import LLMFactory, LLMProvider


async def demo_openshell():
    """Demo OpenShell sandbox execution."""
    print("\n" + "="*60)
    print("🐚 OpenShell Sandbox Demo")
    print("="*60)
    
    # Create sandbox backend
    sandbox = OpenShellBackend()
    print(f"\n[1] OpenShell available: {sandbox._openshell_available}")
    
    # Create sandbox session
    print("\n[2] Creating sandbox session...")
    session = sandbox.create_sandbox("nemotron")
    print(f"    Session ID: {session.session_id}")
    
    # Execute commands in sandbox
    print("\n[3] Executing commands in sandbox...")
    
    result = session.exec("echo 'Hello from sandbox!'")
    print(f"    echo: {result.get('stdout', '').strip()}")
    
    result = session.exec("uname -a")
    print(f"    uname: {result.get('stdout', '').strip()}")
    
    result = session.exec("python3 --version")
    print(f"    python: {result.get('stdout', '').strip()}")
    
    # Run Python code
    print("\n[4] Running Python in sandbox...")
    result = session.run_python("print('Python works! ' + str(2**10))")
    print(f"    Result: {result.get('stdout', '').strip()}")
    
    # Write and read files
    print("\n[5] File operations...")
    session.write("/tmp/test.txt", "Hello from OpenShell!")
    content = session.read("/tmp/test.txt")
    print(f"    Read: {content.strip()}")
    
    # Cleanup
    print("\n[6] Terminating sandbox...")
    session.terminate()
    print("    ✅ Sandbox terminated")
    
    print("\n✅ OpenShell demo complete!")


async def demo_openclaw():
    """Demo OpenClaw orchestration."""
    print("\n" + "="*60)
    print("🦞 OpenClaw Agent Demo")
    print("="*60)
    
    # Create LLM
    llm = LLMFactory.create(LLMProvider.NVIDIA, api_key=os.environ['NVIDIA_API_KEY'])
    
    # Create soul config (like SOUL.md)
    soul = SoulConfig(
        name="Research Analyst",
        emoji="🔍",
        team="AI Research",
        responsibilities=["Research", "Analysis", "Reporting"],
        work_style=["thorough", "accurate"],
        custom_instructions="You are a meticulous research analyst. Always cite sources."
    )
    
    print(f"\n[1] Soul config: {soul.name} {soul.emoji}")
    print(f"    System prompt:\n{soul.to_system_prompt()[:100]}...")
    
    # Create agent
    print("\n[2] Creating OpenClaw agent...")
    agent = OpenClawAgent(
        name="researcher",
        soul=soul,
        llm=llm,
    )
    print(f"    ✅ Agent created: {agent.name}")
    
    # Test with LLM
    print("\n[3] Testing agent with LLM...")
    response = await agent.think("What are the top 3 benefits of AI?")
    print(f"    Response: {response[:150]}...")
    
    # Create crew
    print("\n[4] Creating OpenClaw crew...")
    pm_soul = SoulConfig(name="PM", emoji="📋", responsibilities=["Coordinate", "Delegate"])
    dev_soul = SoulConfig(name="Developer", emoji="💻", responsibilities=["Code", "Build"])
    
    pm = OpenClawAgent(name="pm", soul=pm_soul, llm=llm)
    dev = OpenClawAgent(name="dev", soul=dev_soul, llm=llm)
    
    crew = OpenClawCrew(
        agents=[pm, dev],
        process="sequential"
    )
    print(f"    ✅ Crew with {len(crew.agents)} agents")
    
    # Execute crew
    print("\n[5] Executing crew on task...")
    results = await crew.kickoff("Build a web app")
    print(f"    ✅ Completed {len(results)} tasks")
    
    print("\n✅ OpenClaw demo complete!")


async def demo_full_integration():
    """Full integration demo."""
    print("\n" + "="*60)
    print("🚀 FULL INTEGRATION DEMO")
    print("="*60)
    
    # Setup
    llm = LLMFactory.create(LLMProvider.NVIDIA, api_key=os.environ['NVIDIA_API_KEY'])
    sandbox = OpenShellBackend()
    
    # Create specialized agents
    print("\n[1] Creating specialized agents...")
    
    researcher = OpenClawAgent(
        name="researcher",
        soul=SoulConfig(name="Researcher", emoji="🔬", 
                       responsibilities=["Research", "Gather info"]),
        llm=llm,
    )
    
    developer = OpenClawAgent(
        name="developer",
        soul=SoulConfig(name="Developer", emoji="⚙️",
                       responsibilities=["Code", "Build", "Test"]),
        llm=llm,
    )
    
    # Add sandbox to developer
    developer.sandbox = sandbox
    
    print(f"    ✅ {researcher.name}, {developer.name}")
    
    # Create crew
    crew = OpenClawCrew(
        agents=[researcher, developer],
        process="sequential"
    )
    
    # Execute
    print("\n[2] Running research crew...")
    results = await crew.kickoff("Research Python web frameworks and build a demo")
    print(f"    ✅ Completed {len(results)} tasks")
    
    for name, result in results.items():
        print(f"    {name}: {result[:80]}...")
    
    print("\n✅ Full integration demo complete!")


async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🚀 OpenShell & OpenClaw Integration Demo                  ║
║                                                              ║
║   OpenShell: Isolated sandbox execution                     ║
║   OpenClaw: Multi-agent orchestration                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    await demo_openshell()
    await demo_openclaw()
    await demo_full_integration()
    
    print("\n" + "="*60)
    print("🎉 ALL INTEGRATIONS DEMONSTRATED!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
