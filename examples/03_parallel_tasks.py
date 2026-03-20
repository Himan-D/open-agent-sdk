"""
Example 3: Parallel Execution - Multiple Independent Tasks
Execute tasks concurrently for faster results
"""
import asyncio
from open_agent import create_agent, create_crew


async def main():
    print("=" * 60)
    print("Example 3: Parallel Execution - Concurrent Tasks")
    print("=" * 60)
    
    print("\nCreating agents for parallel execution...")
    
    coder = await create_agent(
        name="coder",
        role="Software Developer",
        goal="Write clean, efficient code",
        backstory="You are an expert programmer who writes elegant solutions.",
    )
    
    tester = await create_agent(
        name="tester",
        role="QA Engineer",
        goal="Ensure code quality through comprehensive testing",
        backstory="You are a thorough QA engineer who catches every bug.",
    )
    
    print("Creating parallel crew...")
    
    crew = create_crew(
        agents_config=[
            {"name": "coder", "role": "Software Developer", 
             "goal": "Write code", "backstory": coder.backstory},
            {"name": "tester", "role": "QA Engineer",
             "goal": "Test code", "backstory": tester.backstory},
        ],
        tasks_config=[
            {
                "description": "Write a Python function to calculate factorial recursively",
                "agent": "coder",
                "expected_output": "Python code for factorial function",
            },
            {
                "description": "Write test cases for a factorial function",
                "agent": "tester",
                "expected_output": "pytest test cases covering edge cases",
            },
        ],
        process="parallel",
        verbose=True,
    )
    
    print("\nExecuting tasks in parallel...")
    results = await crew.kickoff()
    
    print("\n" + "=" * 60)
    print("PARALLEL RESULTS")
    print("=" * 60)
    for task, result in results.items():
        print(f"\n### {task[:50]}...")
        print(result[:500] if len(result) > 500 else result)


if __name__ == "__main__":
    asyncio.run(main())
