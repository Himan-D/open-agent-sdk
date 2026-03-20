"""Example: Using OpenAgent with NVIDIA Nemotron and OpenShell.

This example demonstrates how to create a deep agent with:
- NVIDIA Nemotron as the reasoning model
- OpenShell for secure execution
- Tool calling and planning capabilities
"""

import asyncio
import os
from open_agent import (
    create_deep_agent,
    create_gateway,
    create_nemotron_model,
    SoulConfig,
    ShellTool,
    FileTools,
    TodoTool,
)


async def basic_example():
    """Basic example of using OpenAgent."""
    print("=== Basic OpenAgent Example ===\n")

    # Create an agent with default settings
    agent = create_deep_agent(
        name="assistant",
        model="nvidia/nemotron-3-super-120b-a12b",
        system_prompt="You are a helpful coding assistant.",
        use_openshell=False,  # Disable for basic example
    )

    await agent.initialize()

    # Process a message
    response = await agent.process_message(
        "Hello! Can you help me write a Python function?"
    )
    print(f"Agent: {response}")


async def coding_agent_example():
    """Example of a coding agent with shell and file tools."""
    print("\n=== Coding Agent Example ===\n")

    # Create a specialized coding agent
    soul = SoulConfig(
        name="Code Assistant",
        emoji="",
        team="Engineering",
        responsibilities=[
            "Write and debug code",
            "Review code changes",
            "Explain technical concepts",
        ],
        constraints=[
            "Always verify code before executing",
            "Provide clear explanations",
        ],
    )

    agent = create_deep_agent(
        name="coding-agent",
        model="nvidia/nemotron-3-super-120b-a12b",
        soul=soul,
        system_prompt="""You are an expert Python programmer. 
You have access to shell commands and file operations.
Always write clean, well-documented code.""",
        use_openshell=True,
    )

    await agent.initialize()

    # Process a coding request
    response = await agent.process_message(
        "Create a simple web server in Python using Flask."
    )
    print(f"Agent: {response}")


async def gateway_example():
    """Example of running the gateway server."""
    print("\n=== Gateway Example ===\n")

    # Create gateway
    gateway = create_gateway(
        name="my-gateway",
        port=8080,
        enable_http=True,
        enable_websocket=True,
    )

    # Register an agent
    agent = create_deep_agent(name="default")
    gateway.register_agent(agent)

    print("Gateway configured. Start with:")
    print("  open-agent gateway start")


async def multi_model_example():
    """Example showing multiple model options."""
    print("\n=== Multi-Model Example ===\n")

    # Different model options via LangChain NVIDIA integration
    from open_agent.models.nemotron import create_nemotron_model

    # Nemotron Super (most capable)
    nemotron_super = create_nemotron_model(
        model_name="nvidia/nemotron-3-super-120b-a12b",
        temperature=0.7,
    )
    print("Created Nemotron Super model")

    # Nemotron Nano (faster, smaller)
    nemotron_nano = create_nemotron_model(
        model_name="nvidia/nemotron-3-nano-8b",
        temperature=0.7,
    )
    print("Created Nemotron Nano model")


async def main():
    """Run all examples."""
    # Check for API key
    if not os.environ.get("NVIDIA_API_KEY"):
        print("Warning: NVIDIA_API_KEY not set")
        print("Set it with: export NVIDIA_API_KEY=your_key")
        print("\nRunning basic example without API calls...\n")

    try:
        await basic_example()
        await gateway_example()
        await multi_model_example()
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: You need to install dependencies:")
        print("  pip install -e .")


if __name__ == "__main__":
    asyncio.run(main())
