"""
Example 1: Basic Agent - Single AI assistant using NVIDIA Nemotron
"""
import asyncio
from open_agent import create_agent


async def main():
    print("=" * 60)
    print("Example 1: Basic Agent with NVIDIA Nemotron")
    print("=" * 60)
    
    agent = await create_agent(
        name="assistant",
        role="AI Assistant",
        goal="Help users with their questions accurately and efficiently",
        backstory="""You are a highly capable AI assistant. You have access to tools
        for calculations, web search, and Python code execution. Use them when needed
        to provide accurate answers.""",
        provider="nvidia",
    )
    
    print("\nAgent ready! Ask me anything...")
    
    while True:
        question = input("\nYou: ")
        if question.lower() in ['exit', 'quit', 'q']:
            break
        
        result = await agent.execute(question)
        print(f"\nAssistant: {result}")


if __name__ == "__main__":
    asyncio.run(main())
