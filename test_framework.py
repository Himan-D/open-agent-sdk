"""Test OpenAgent framework."""
import asyncio
import os

# Set a mock API key for testing structure
os.environ.setdefault("NVIDIA_API_KEY", "test_key_for_structure")

from open_agent import (
    create_deep_agent,
    create_gateway,
    SoulConfig,
    DeepAgent,
    Gateway,
)


def test_imports():
    """Test that all imports work."""
    print("✓ All imports successful")
    print("  - DeepAgent")
    print("  - Gateway")
    print("  - SoulConfig")
    print("  - create_deep_agent")
    print("  - create_gateway")


async def test_agent_creation():
    """Test creating an agent."""
    agent = create_deep_agent(
        name="test-agent",
        model="nvidia/nemotron-3-super-120b-a12b",
        system_prompt="You are a test assistant.",
        use_openshell=False,  # Disable for testing
    )
    print(f"✓ Agent created: {agent.name}")
    print(f"  - Model: {agent.config.agent.model if hasattr(agent, 'config') else agent.nemotron}")
    return agent


async def test_soul_config():
    """Test SoulConfig like OpenClaw."""
    soul = SoulConfig(
        name="Research Agent",
        emoji="",
        team="Analysis",
        responsibilities=[
            "Conduct research",
            "Write reports",
            "Present findings",
        ],
        constraints=[
            "Cite sources",
            "Be objective",
        ],
    )
    
    agent = create_deep_agent(
        name="researcher",
        soul=soul,
        use_openshell=False,
    )
    print(f"✓ SoulConfig created agent: {agent.name}")
    return agent


async def test_gateway():
    """Test Gateway creation."""
    gateway = create_gateway(
        name="test-gateway",
        port=8080,
        enable_http=False,  # Disable for testing
        enable_websocket=False,
    )
    
    # Register an agent
    agent = create_deep_agent(name="gateway-agent", use_openshell=False)
    gateway.register_agent(agent)
    
    agents = gateway.list_agents()
    print(f"✓ Gateway created with {len(agents)} agent(s)")
    print(f"  - Agents: {[a['name'] for a in agents]}")
    print(f"  - Stats: {gateway.get_stats()}")


async def test_models():
    """Test Nemotron model creation."""
    from open_agent.models.nemotron import get_available_nemotron_models
    
    models = get_available_nemotron_models()
    print(f"✓ Available Nemotron models: {len(models)}")
    for model in models[:3]:
        print(f"  - {model}")


def compare_with_openclaw():
    """Compare our framework with OpenClaw."""
    print("\n" + "="*60)
    print("COMPARISON: OpenAgent vs OpenClaw")
    print("="*60)
    
    comparison = """
    | Feature                    | OpenClaw        | OpenAgent       |
    |----------------------------|-----------------|-----------------|
    | Language                   | TypeScript/JS   | Python          |
    | LLM Support                | Claude, GPT     | Nemotron, Any   |
    | Sandbox/Security           | OpenShell       | OpenShell       |
    | Agent Definition           | SOUL.md files   | SoulConfig code |
    | Memory                     | MEMORY.md       | Memory system   |
    | Multi-agent                | Teams/Hierarchy | Subagents       |
    | Gateway                    | Built-in        | Built-in        |
    | Channel adapters           | 10+ platforms   | HTTP/WS only    |
    | Configuration              | JSON/YAML       | Pydantic        |
    | Framework                  | Custom          | LangChain       |
    | Maturity                   | Production      | Beta            |
    | Installation               | npm install     | pip install     |
    | CLI                        | openclaw        | open-agent      |
    """
    print(comparison)
    
    print("\nKEY DIFFERENCES:")
    print("  OpenClaw:")
    print("    ✓ Production-ready, battle-tested")
    print("    ✓ Rich channel integrations (WhatsApp, Slack, Discord)")
    print("    ✓ File-based agent definition (Markdown)")
    print("    ✓ Large community and ecosystem")
    print()
    print("  OpenAgent:")
    print("    ✓ Python-native (LangChain ecosystem)")
    print("    ✓ NVIDIA Deep Agents integration")
    print("    ✓ Nemotron models optimized for agents")
    print("    ✓ Easier to extend/customize in Python")
    print("    ⚠ Less mature, fewer integrations")


async def main():
    """Run all tests."""
    print("="*60)
    print("OpenAgent Framework Test")
    print("="*60 + "\n")
    
    test_imports()
    print()
    
    await test_agent_creation()
    print()
    
    await test_soul_config()
    print()
    
    await test_gateway()
    print()
    
    test_models()
    print()
    
    compare_with_openclaw()
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
