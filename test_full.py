"""Full test of OpenAgent with NVIDIA API."""
import asyncio
import os

async def test_agent_capabilities():
    """Test various agent capabilities."""
    from open_agent import create_deep_agent, SoulConfig, AgentContext
    
    print("="*60)
    print("OpenAgent Full Test with NVIDIA Nemotron")
    print("="*60)
    
    # Create agent with SoulConfig (OpenClaw-style)
    soul = SoulConfig(
        name="Coding Assistant",
        emoji="",
        team="Engineering",
        responsibilities=[
            "Write clean, efficient code",
            "Debug and fix issues",
            "Explain technical concepts",
        ],
        constraints=[
            "Always verify code works",
            "Be concise in responses",
        ],
    )
    
    agent = create_deep_agent(
        name="coding-agent",
        model="nvidia/nemotron-3-super-120b-a12b",
        soul=soul,
        system_prompt="You are an expert Python programmer. Write clean, well-documented code.",
        use_openshell=False,  # Disable for API test
    )
    
    await agent.initialize()
    print(f"\n✓ Agent initialized: {agent.name}")
    print(f"✓ System prompt built from SoulConfig")
    
    context = AgentContext(session_id="test-session")
    
    # Test 1: Simple math
    print("\n" + "-"*40)
    print("Test 1: Simple Math")
    print("-"*40)
    response = await agent.process_message("What is 15 * 23?", context)
    print(f"Question: What is 15 * 23?")
    print(f"Answer: {response}")
    
    # Test 2: Code generation
    print("\n" + "-"*40)
    print("Test 2: Code Generation")
    print("-"*40)
    response = await agent.process_message(
        "Write a Python function to check if a string is a palindrome. Keep it brief.",
        context
    )
    print(f"Question: Write palindrome function")
    print(f"Answer:\n{response[:500]}...")
    
    # Test 3: Explanation
    print("\n" + "-"*40)
    print("Test 3: Technical Explanation")
    print("-"*40)
    response = await agent.process_message(
        "Explain what a decorator does in Python in one sentence.",
        context
    )
    print(f"Question: Explain Python decorator")
    print(f"Answer: {response}")
    
    # Test 4: Multi-turn conversation
    print("\n" + "-"*40)
    print("Test 4: Multi-turn Conversation")
    print("-"*40)
    await agent.process_message("My favorite color is blue.", context)
    response = await agent.process_message("What's my favorite color?", context)
    print(f"Q1: My favorite color is blue.")
    print(f"Q2: What's my favorite color?")
    print(f"A: {response}")
    
    # Test 5: Memory
    print("\n" + "-"*40)
    print("Test 5: Memory Check")
    print("-"*40)
    messages = agent.get_memory("test-session")
    print(f"Conversation history: {len(messages)} messages")
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_agent_capabilities())
