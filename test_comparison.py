"""Comparison test between OpenAgent and OpenClaw."""

import asyncio
import os

async def test_openagent_message():
    """Test OpenAgent with a message."""
    from open_agent import create_deep_agent, AgentContext
    
    print("\n" + "="*60)
    print("OpenAgent Test")
    print("="*60)
    
    os.environ.setdefault("NVIDIA_API_KEY", "test")
    
    agent = create_deep_agent(
        name="test-agent",
        model="nvidia/nemotron-3-super-120b-a12b",
        system_prompt="You are a helpful assistant. Be concise.",
        use_openshell=False,
    )
    
    await agent.initialize()
    
    print(f"\n✓ Agent created: {agent.name}")
    print(f"✓ Model: {agent.nemotron.model_name if hasattr(agent.nemotron, 'model_name') else 'nemotron'}")
    
    # Try to process a message
    context = AgentContext(session_id="test-session")
    try:
        response = await agent.process_message("What is 2+2?")
        print(f"\nUser: What is 2+2?")
        print(f"Agent: {response[:200]}...")
    except Exception as e:
        print(f"\n⚠ API call failed (expected without valid API key): {str(e)[:100]}")
    
    return agent


def test_openclaw():
    """Test OpenClaw setup."""
    print("\n" + "="*60)
    print("OpenClaw Test")
    print("="*60)
    
    # Check OpenClaw config
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(config_path):
        print(f"\n✓ Config found: {config_path}")
    else:
        print(f"\n⚠ Config not found at {config_path}")
        print("  Run 'openclaw init' to set up OpenClaw")
    
    # Check workspace
    workspace_path = os.path.expanduser("~/.openclaw/workspace")
    if os.path.exists(workspace_path):
        files = os.listdir(workspace_path)
        print(f"✓ Workspace exists: {workspace_path}")
        if files:
            print(f"  Files: {', '.join(files[:5])}")
    else:
        print(f"⚠ Workspace not found")


async def main():
    """Run comparison tests."""
    print("="*60)
    print("OpenAgent vs OpenClaw - Feature Comparison")
    print("="*60)
    
    # Test OpenAgent
    await test_openagent_message()
    
    # Test OpenClaw
    test_openclaw()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    print("""
    | Aspect               | OpenAgent                    | OpenClaw                    |
    |---------------------|------------------------------|----------------------------|
    | **Setup**           | pip install + API key       | npm install + config        |
    | **Languages**       | Python                       | TypeScript/JavaScript       |
    | **LLM**             | Nemotron (NVIDIA)           | Claude, GPT, Gemini         |
    | **Security**        | OpenShell sandbox           | OpenShell sandbox           |
    | **Agent Config**    | Code (SoulConfig)           | Markdown files (SOUL.md)   |
    | **Memory**          | In-memory + persistence      | MEMORY.md + ChromaDB       |
    | **Multi-agent**     | Subagent spawning            | Teams + hierarchy           |
    | **Channels**        | HTTP/WebSocket               | 10+ platforms              |
    | **Production**      | Beta                         | Production-ready           |
    | **Ecosystem**       | LangChain                    | npm community               |
    """)
    
    print("\n**Key Observations:**")
    print("  1. OpenClaw is more mature with production deployments")
    print("  2. OpenAgent leverages LangChain/DeepAgents for flexibility")
    print("  3. Both use OpenShell for security sandboxing")
    print("  4. OpenClaw has richer integrations (Slack, Discord, etc)")
    print("  5. OpenAgent is Python-native for ML/data integrations")
    print("  6. OpenClaw's file-based config is more user-friendly")


if __name__ == "__main__":
    asyncio.run(main())
