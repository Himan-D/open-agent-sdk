"""
Example 2: Multi-Agent Crew - Research and Write Pipeline
CrewAI-style orchestration with sequential task execution
"""
import asyncio
from open_agent import create_agent, create_crew


async def main():
    print("=" * 60)
    print("Example 2: Multi-Agent Crew - Research & Write Pipeline")
    print("=" * 60)
    
    print("\nCreating agents...")
    
    researcher = await create_agent(
        name="researcher",
        role="Research Specialist",
        goal="Research topics thoroughly and provide comprehensive information",
        backstory="""You are an expert researcher with decades of experience in
        finding and synthesizing information. You excel at identifying key facts,
        trends, and insights from various sources.""",
        provider="nvidia",
    )
    
    writer = await create_agent(
        name="writer",
        role="Content Writer",
        goal="Create engaging, well-structured content from research",
        backstory="""You are a skilled content writer who transforms complex
        information into clear, engaging narratives. Your writing captivates
        readers while maintaining accuracy and depth.""",
        provider="nvidia",
    )
    
    print("Agents created: researcher, writer")
    
    topic = input("\nEnter a topic to research: ") or "The future of AI agents in software development"
    
    print(f"\nCreating crew for topic: {topic}")
    
    crew = create_crew(
        agents_config=[
            {
                "name": "researcher",
                "role": "Research Specialist",
                "goal": "Research topics thoroughly",
                "backstory": researcher.backstory,
            },
            {
                "name": "writer",
                "role": "Content Writer",
                "goal": "Create engaging content",
                "backstory": writer.backstory,
            },
        ],
        tasks_config=[
            {
                "description": f"Research comprehensive information about: {topic}",
                "agent": "researcher",
                "expected_output": "Detailed research summary with key points and sources",
            },
            {
                "description": "Write an engaging article based on the research",
                "agent": "writer",
                "expected_output": "Well-structured article with introduction, body, and conclusion",
            },
        ],
        process="sequential",
        verbose=True,
    )
    
    print("\nStarting crew execution...")
    print("-" * 40)
    
    results = await crew.kickoff()
    
    print("\n" + "=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(results[list(results.keys())[-1]])


if __name__ == "__main__":
    asyncio.run(main())
