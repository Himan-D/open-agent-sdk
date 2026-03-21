#!/usr/bin/env python3
"""Agentic Agent Demo - Watch the AI Think Like an AGI.

This demo shows:
1. ReAct loop: Observe -> Reason -> Plan -> Act -> Reflect
2. Chain of Thought reasoning  
3. Self-reflection and self-correction
4. Working memory
5. Multi-agent collaboration
6. Tool execution
"""
import asyncio
import sys
import time

sys.path.insert(0, "/Users/himand/open-agent/src")


async def demo_single_agentic():
    """Demo 1: Single agent with full reasoning."""
    print("\n" + "="*70)
    print("  DEMO 1: Agentic Agent Thinking")
    print("="*70)
    
    from smith_ai.agentic import AgenticAgent, ThinkStep, ReasoningEngine
    
    # Create a simple tool
    def calculator(expression: str) -> str:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Calculation result: {result}"
        except Exception as e:
            return f"Error: {e}"
    
    tools = {
        "calculator": calculator,
    }
    
    # Create agentic agent (no LLM needed - uses symbolic reasoning)
    agent = AgenticAgent(
        name="Aria",
        role="Problem Solver",
        goal="Solve complex problems by thinking step by step",
        tools=tools,
        verbose=True,
        thinking_depth=3,
    )
    
    print("\n" + "-"*70)
    print("  Task: Calculate 25 + 17 * 3 - 100 / 4")
    print("-"*70 + "\n")
    
    result = await agent.run("Calculate 25 + 17 * 3 - 100 / 4")
    
    print("\n" + "-"*70)
    print("  Task: What is the capital of France?")
    print("-"*70 + "\n")
    
    result2 = await agent.run("What is the capital of France?")
    
    print("\n" + "-"*70)
    print("  Task: Search the web for latest AI news")
    print("-"*70 + "\n")
    
    result3 = await agent.run("Search the web for latest AI news")
    
    return agent


async def demo_reasoning_engine():
    """Demo 2: Show the reasoning engine capabilities."""
    print("\n" + "="*70)
    print("  DEMO 2: Reasoning Engine (Chain of Thought)")
    print("="*70)
    
    from smith_ai.agentic import ReasoningEngine, ThinkStep, WorkingMemory
    
    engine = ReasoningEngine()
    
    # Observe
    obs = engine.observe("User asked to solve a complex math problem")
    print(f"\n[OBSERVE] {obs}")
    
    # Reason step by step
    thoughts = engine.reason("What is the best way to solve 2 + 2?", max_steps=5)
    print(f"\n[REASON] Chain of thought ({len(thoughts)} steps):")
    for i, thought in enumerate(thoughts, 1):
        print(f"  Step {i}: {thought[:60]}...")
    
    # Plan
    plan = engine.plan("Solve 2 + 2", ["calculator", "web_search"])
    print(f"\n[PLAN] Plan created with {len(plan)} steps:")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step.action} (tool: {step.tool})")
    
    # Reflect
    reflection = engine.reflect("2 + 2 = 4", expected="4")
    print(f"\n[REFLECT] {reflection[:100]}...")
    
    # Decompose goal
    goal = engine.decompose_goal("Build a website")
    print(f"\n[DECOMPOSE] Goal: {goal.description}")
    print(f"  Subgoals: {len(goal.subgoals)}")
    for sg in goal.subgoals:
        print(f"    - {sg.description}")
    
    return engine


async def demo_working_memory():
    """Demo 3: Working memory and context."""
    print("\n" + "="*70)
    print("  DEMO 3: Working Memory System")
    print("="*70)
    
    from smith_ai.agentic import WorkingMemory, ThinkStep
    
    memory = WorkingMemory()
    
    # Add observations
    memory.add_observation("User asked about Python")
    memory.add_observation("Python is a programming language")
    memory.add_observation("It's used for AI/ML")
    
    # Add reflections
    memory.add_reflection("The user seems interested in AI")
    memory.add_reflection("I should recommend Python resources")
    
    # Add learnings
    memory.add_learning("Python + AI is a powerful combination")
    memory.add_learning("SmithAI uses Python 3.10+")
    
    # Add thoughts
    memory.add_thought(ThinkStep.REASON, "Breaking down the problem...", confidence=0.7)
    memory.add_thought(ThinkStep.PLAN, "Creating a plan to help", confidence=0.6)
    memory.add_thought(ThinkStep.ACT, "Executing the plan", confidence=0.8)
    
    print(f"\n[MEMORY] Stats:")
    print(f"  Observations: {len(memory.observations)}")
    print(f"  Reflections: {len(memory.reflections)}")
    print(f"  Learnings: {len(memory.learnings)}")
    print(f"  Thoughts: {len(memory.thoughts)}")
    
    print(f"\n[MEMORY] Context summary:")
    print(memory.get_context_summary())
    
    print(f"\n[MEMORY] Thought chain:")
    for thought in memory.thoughts:
        print(f"  [{thought.step.value}] {thought.content[:50]}... (conf: {thought.confidence})")
    
    return memory


async def demo_multi_agent():
    """Demo 4: Multi-agent collaboration."""
    print("\n" + "="*70)
    print("  DEMO 4: Multi-Agent Collaboration")
    print("="*70)
    
    from smith_ai.agentic import AgenticAgent, MultiAgentCrew
    
    # Create specialized agents
    researcher = AgenticAgent(
        name="Researcher",
        role="Research Specialist",
        goal="Find and analyze information thoroughly",
        verbose=False,
    )
    
    analyst = AgenticAgent(
        name="Analyst",
        role="Data Analyst", 
        goal="Analyze data and find patterns",
        verbose=False,
    )
    
    writer = AgenticAgent(
        name="Writer",
        role="Technical Writer",
        goal="Present information clearly",
        verbose=False,
    )
    
    # Create crew
    crew = MultiAgentCrew(
        agents=[researcher, analyst, writer],
        verbose=True,
    )
    
    # Solve a problem collaboratively
    result = await crew.solve(
        "Analyze the benefits of AI agents in software development"
    )
    
    print(f"\n[CREW] Completed with {len(result)} results")
    for name, res in result.items():
        if name != "synthesis":
            print(f"  [{name}] thoughts: {res.get('iterations', 0)} iterations")
    
    return crew


async def demo_with_llm():
    """Demo 5: Agentic agent with LLM (if API key available)."""
    print("\n" + "="*70)
    print("  DEMO 5: Agentic Agent with Real LLM")
    print("="*70)
    
    import os
    from smith_ai.agentic import AgenticAgent
    
    llm = None
    if os.getenv("OPENAI_API_KEY"):
        from smith_ai.llm import create_llm
        llm = create_llm("openai", model="gpt-4o-mini")
        print("\n[LLM] Using OpenAI GPT-4o-mini")
    elif os.getenv("ANTHROPIC_API_KEY"):
        from smith_ai.llm import create_llm
        llm = create_llm("anthropic", model="claude-3-5-haiku-20241022")
        print("\n[LLM] Using Anthropic Claude")
    else:
        print("\n[LLM] No API key found - using symbolic reasoning fallback")
        print("      Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable LLM")
    
    agent = AgenticAgent(
        name="Sage",
        role="AI Assistant",
        goal="Help users with complex tasks",
        llm=llm,
        verbose=True,
    )
    
    if llm:
        result = await agent.run(
            "Explain why the sky is blue in 3 sentences."
        )
        print(f"\n[RESULT] {result['output'][:200]}...")
    else:
        result = await agent.run(
            "Think about why the sky is blue."
        )
        print(f"\n[RESULT] {result['output'][:300]}...")


async def demo_agi_characteristics():
    """Demo 6: AGI-like characteristics."""
    print("\n" + "="*70)
    print("  DEMO 6: AGI-Like Characteristics")
    print("="*70)
    
    from smith_ai.agentic import (
        AgenticAgent, ReasoningEngine, WorkingMemory,
        ThinkStep, Goal, PlanStep
    )
    
    agent = AgenticAgent(
        name="AGI-Demo",
        role="AGI Prototype",
        goal="Demonstrate AGI-like thinking",
        verbose=False,
    )
    
    print("""
[AGI Characteristics Implemented]

1. AUTONOMY: Agent can operate independently
   - Makes decisions without human intervention
   - Plans and executes actions
   
2. REASONING: Chain of Thought reasoning
   - Thinks step by step before acting
   - Maintains reasoning trace
   
3. PLANNING: Goal decomposition
   - Breaks complex goals into subgoals
   - Creates execution plans
   
4. MEMORY: Working and long-term memory
   - Tracks observations
   - Stores reflections and learnings
   
5. LEARNING: Improves from experience
   - Records execution patterns
   - Adapts approach based on results
   
6. TOOL USE: Uses tools effectively
   - Knows when to use tools
   - Learns from tool execution
   
7. SELF-REFLECTION: Evaluates own performance
   - Assesses confidence
   - Corrects errors
""")
    
    # Demonstrate goal decomposition
    print("\n[Goal Decomposition Demo]")
    engine = ReasoningEngine()
    goal = engine.decompose_goal("Build a complete AI agent framework")
    print(f"Main Goal: {goal.description}")
    print("Decomposed into:")
    for i, sg in enumerate(goal.subgoals, 1):
        print(f"  {i}. {sg.description}")
    
    return agent


async def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   █████╗ ██████╗  ██████╗██╗  ██╗ █████╗ ███╗   ██╗███████╗██████╗ ║
║  ██╔══██╗██╔══██╗██╔════╝██║  ██║██╔══██╗████╗  ██║██╔════╝██╔══██╗║
║  ███████║██████╔╝██║     ███████║███████║██╔██╗ ██║█████╗  ██████╔╝║
║  ██╔══██║██╔══██╗██║     ██╔══██║██╔══██║██║╚██╗██║██╔══╝  ██╔══██╗║
║  ██║  ██║██║  ██║╚██████╗██║  ██║██║  ██║██║ ╚████║███████╗██║  ██║║
║  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝║
║                                                                      ║
║   A G I   -   A g e n t i c   A I   F r a m e w o r k               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("""
This demo shows SmithAI's AGI-like capabilities:

  1. Agentic Agent - Full reasoning with ReAct loop
  2. Reasoning Engine - Chain of Thought reasoning
  3. Working Memory - Context tracking
  4. Multi-Agent Collaboration - Multiple agents working together
  5. LLM Integration - With real AI backend (if API key available)
  6. AGI Characteristics - Autonomy, reasoning, planning, memory, learning
""")
    
    demos = [
        ("Agentic Thinking", demo_single_agentic),
        ("Reasoning Engine", demo_reasoning_engine),
        ("Working Memory", demo_working_memory),
        ("Multi-Agent Crew", demo_multi_agent),
        ("LLM Integration", demo_with_llm),
        ("AGI Characteristics", demo_agi_characteristics),
    ]
    
    results = []
    for name, demo_fn in demos:
        try:
            await demo_fn()
            results.append((name, True))
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("  FINAL SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, ok in results if ok)
    print(f"\nDemos passed: {passed}/{len(results)}")
    
    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {name}")
    
    print("\n" + "="*70)
    print("  AGI-Like Features Demo Complete!")
    print("="*70)
    print("""
Next steps to build toward AGI:
1. Add more reasoning capabilities (induction, deduction)
2. Implement continuous learning from interactions  
3. Add theory of mind (understanding other agents)
4. Enable self-modification of code/weights
5. Scale to handle any task (universal)
    """)


if __name__ == "__main__":
    asyncio.run(main())
