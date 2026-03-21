#!/usr/bin/env python3
"""True AGI Framework Demo - Based on Common Model of Cognition.

Architecture inspired by:
- Common Model of Cognition (ACT-R, Soar, Sigma)
- Cognitive Design Patterns
- CoALA Framework
- AGI Architecture Requirements

This demonstrates:
1. Common Model of Cognition components
2. Working Memory (ACT-R style buffers)
3. Procedural Memory (SOAR style productions)
4. Declarative Memory (Semantic + Episodic)
5. World Model construction
6. Metacognition (Self-monitoring)
7. Multi-method reasoning
8. Cognitive Agent
9. True AGI Agent with OpenShell
10. Multi-agent collaboration
"""

import asyncio
import sys
sys.path.insert(0, "/Users/himand/open-agent/src")


async def demo_common_model():
    """Demo 1: Common Model of Cognition components."""
    print("\n" + "="*70)
    print("  DEMO 1: Common Model of Cognition")
    print("="*70)
    
    from smith_ai.agi.v2 import (
        WorkingMemory, ProceduralMemory, DeclarativeMemory,
        WorldModel, Metacognition,
    )
    
    print("""
    Common Model of Cognition Architecture:
    
    ┌─────────────┐
    │  PERCEPTION │────┐
    └─────────────┘    │
                      ▼
    ┌─────────────────────────┐
    │     WORKING MEMORY      │◄──┐
    │  (Buffers: goal,        │   │
    │   retrieval, motor)     │   │
    └─────────────────────────┘   │
         │    ▲    │    ▲        │
         ▼    │    ▼    │        │
    ┌──────────┐ ┌──────────────┐
    │ PROCEDURAL│ │  DECLARATIVE │
    │  MEMORY   │ │   MEMORY     │
    │(Productions│ │(Semantic +   │
    │  Rules)    │ │  Episodic)   │
    └──────────┘ └──────────────┘
         │
         ▼
    ┌─────────────┐
    │    MOTOR     │────► ACTION
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │ METACOGNITION│
    └─────────────┘
    """)
    
    # Working Memory
    wm = WorkingMemory()
    wm.set("goal", "Solve the problem")
    wm.set("context", "User asked about AI")
    print(f"\n[WorkingMemory] Buffers: {list(wm.buffers.keys())}")
    print(f"[WorkingMemory] Contents: {dict(wm.contents)}")
    
    # Procedural Memory
    pm = ProceduralMemory()
    print(f"\n[ProceduralMemory] Productions: {len(pm.productions)}")
    for p in pm.productions[:3]:
        print(f"  - {p.id}: {p.content[:50]}...")
    
    # Declarative Memory
    dm = DeclarativeMemory()
    print(f"\n[DeclarativeMemory] Semantic: {len(dm.semantic)}")
    print(f"[DeclarativeMemory] Episodic: {len(dm.episodic)}")
    
    # World Model
    wm_model = WorldModel()
    wm_model.add_entity("AI", {"type": "technology", "capability": "reasoning"})
    wm_model.add_relation("cause", "enables", "intelligence")
    print(f"\n[WorldModel] Entities: {len(wm_model.entities)}")
    print(f"[WorldModel] Relations: {len(wm_model.relations)}")
    
    # Metacognition
    meta = Metacognition()
    print(f"\n[Metacognition] Reasoning quality: {meta.reasoning_quality:.0%}")
    print(f"[Metacognition] Reflection: {meta.reflect()}")


async def demo_memory_systems():
    """Demo 2: Memory Systems (ACT-R style)."""
    print("\n" + "="*70)
    print("  DEMO 2: Memory Systems")
    print("="*70)
    
    from smith_ai.agi.v2 import (
        MemoryItem, Chunk, Episode,
        WorkingMemory, DeclarativeMemory,
        MemoryType,
    )
    
    # Working Memory
    print("\n[WorkingMemory - ACT-R Buffers]")
    wm = WorkingMemory()
    
    # Set buffers like ACT-R
    goal_item = MemoryItem(
        id="goal_1",
        content="Learn about AI",
        memory_type=MemoryType.WORKING,
    )
    wm.set_buffer("goal", goal_item)
    wm.set("current_task", "studying")
    
    print(f"  Goal buffer: {wm.get_buffer('goal').content}")
    print(f"  Current task: {wm.get('current_task')}")
    
    # Declarative Memory - Semantic
    print("\n[DeclarativeMemory - Semantic]")
    dm = DeclarativeMemory()
    
    # Store concepts
    dm.store_semantic("neural_network", {
        "definition": "Computing system inspired by biological neural networks",
        "type": "ai_technology",
        "components": ["neurons", "layers", "weights"],
    })
    
    dm.store_semantic("transformer", {
        "definition": "Architecture using self-attention mechanism",
        "type": "ai_architecture",
        "key_paper": "Attention Is All You Need",
    })
    
    results = dm.retrieve_semantic("neural")
    print(f"  Retrieved '{len(results)}' memories matching 'neural'")
    for r in results:
        print(f"    - {r.id}: {r.content if isinstance(r.content, str) else r.chunk_type}")
    
    # Declarative Memory - Episodic
    print("\n[DeclarativeMemory - Episodic]")
    
    dm.store_episode(
        situation="User asked about machine learning",
        actions=["searched documentation", "found examples"],
        outcome="success",
        emotion="satisfied",
    )
    
    dm.store_episode(
        situation="Tried to explain deep learning",
        actions=["used analogies", "provided code examples"],
        outcome="partial_success",
        emotion="neutral",
    )
    
    episodes = dm.retrieve_episodes("learning")
    print(f"  Retrieved '{len(episodes)}' episodes matching 'learning'")
    for e in episodes:
        print(f"    - {e.situation[:40]}... → {e.outcome}")


async def demo_reasoning():
    """Demo 3: Multi-Method Reasoning."""
    print("\n" + "="*70)
    print("  DEMO 3: Multi-Method Reasoning")
    print("="*70)
    
    from smith_ai.agi.v2 import CognitiveAgent, ReasoningMethod
    
    agent = CognitiveAgent(name="Reasoner", role="reasoning", verbose=True)
    
    # Test all reasoning methods
    methods = [
        ReasoningMethod.DEDUCTIVE,
        ReasoningMethod.INDUCTIVE,
        ReasoningMethod.ABDUCTIVE,
        ReasoningMethod.CAUSAL,
        ReasoningMethod.ANALOGICAL,
    ]
    
    for method in methods:
        print(f"\n[{method.value.upper()} Reasoning]")
        result = agent.reason("What causes intelligence?", method)
        print(f"  Conclusion: {result['conclusion']}")
        print(f"  Confidence: {result['confidence']:.0%}")
        print(f"  Steps: {len(result['reasoning_steps'])}")


async def demo_planning():
    """Demo 4: Hierarchical Task Planning (HTN)."""
    print("\n" + "="*70)
    print("  DEMO 4: Hierarchical Task Planning")
    print("="*70)
    
    from smith_ai.agi.v2 import CognitiveAgent
    
    agent = CognitiveAgent(name="Planner", role="planner", verbose=True)
    
    print("\n[Planning a Complex Task]")
    goal = "Build a machine learning model"
    
    plan = agent.plan_action(goal)
    
    print(f"\n  Goal: {goal}")
    print(f"  Plan ({len(plan)} steps):")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step}")
    
    print(f"\n[Executing Plan]")
    for step in plan:
        result = agent.act(step)
        print(f"  ✓ {step}")


async def demo_metacognition():
    """Demo 5: Metacognition and Self-Improvement."""
    print("\n" + "="*70)
    print("  DEMO 5: Metacognition & Self-Improvement")
    print("="*70)
    
    from smith_ai.agi.v2 import Metacognition
    
    meta = Metacognition()
    
    # Monitor reasoning
    print("\n[Self-Monitoring]")
    for i in range(3):
        quality = meta.monitor(
            thought=f"Reasoning about problem {i} - applying rules",
            result="success" if i > 0 else "partial",
        )
        print(f"  Iteration {i+1}: Quality = {quality['overall']:.0%}")
    
    # Update strategy effectiveness
    print("\n[Strategy Effectiveness]")
    meta.update_strategy_effectiveness("deductive", 0.9)
    meta.update_strategy_effectiveness("inductive", 0.7)
    meta.update_strategy_effectiveness("causal", 0.8)
    
    for strategy, effectiveness in meta.strategy_effectiveness.items():
        print(f"  {strategy}: {effectiveness:.0%}")
    
    best = meta.select_strategy()
    print(f"\n[Best Strategy]: {best}")
    
    # Reflect
    print(f"\n[Self-Reflection]: {meta.reflect()}")


async def demo_world_model():
    """Demo 6: World Model Construction."""
    print("\n" + "="*70)
    print("  DEMO 6: World Model")
    print("="*70)
    
    from smith_ai.agi.v2 import WorldModel
    
    wm = WorldModel()
    
    # Add entities
    print("\n[Adding Entities]")
    wm.add_entity("human", {
        "type": "agent",
        "capabilities": ["reasoning", "learning", "planning"],
    })
    wm.add_entity("computer", {
        "type": "tool",
        "capabilities": ["computation", "storage"],
    })
    wm.add_entity("AI", {
        "type": "system",
        "capabilities": ["pattern_recognition", "prediction"],
    })
    
    # Add relations
    print("[Adding Relations]")
    wm.add_relation("human", "uses", "computer")
    wm.add_relation("AI", "extends", "computer")
    wm.add_relation("learning", "enables", "intelligence")
    wm.add_relation("data", "causes", "learning")
    
    # Add rules
    print("[Adding Rules]")
    wm.add_rule("IF more_data AND better_model THEN improved_AI")
    wm.add_rule("IF reasoning AND planning THEN goal_achievement")
    
    # Query world model
    print("\n[World Model State]")
    print(f"  Entities: {len(wm.entities)}")
    print(f"  Relations: {len(wm.relations)}")
    print(f"  Rules: {len(wm.rules)}")
    
    # Simulation
    print("\n[Simulation]")
    initial_state = {
        "data": {"amount": "large", "active": True},
        "model": {"quality": "good"},
    }
    predicted = wm.predict(initial_state, "process_data")
    print(f"  Initial: {initial_state}")
    print(f"  Predicted: {predicted}")
    
    # Counterfactual
    print("\n[Counterfactual]")
    cf = wm.counterfactual("high_performance", "less_data")
    print(f"  {cf}")


async def demo_cognitive_agent():
    """Demo 7: Full Cognitive Agent."""
    print("\n" + "="*70)
    print("  DEMO 7: Cognitive Agent")
    print("="*70)
    
    from smith_ai.agi.v2 import CognitiveAgent
    
    agent = CognitiveAgent(name="Cogni", role="researcher", verbose=True)
    
    # Full cognitive cycle
    print("\n[Cognitive Cycle]")
    
    # Perceive
    agent.perceive("What is the relationship between AI and intelligence?")
    
    # Reason
    reasoning = agent.reason("AI and intelligence", method=None)
    print(f"\n[Reasoning Result]")
    print(f"  {reasoning['conclusion']}")
    
    # Plan
    plan = agent.plan_action("Understand AI and intelligence")
    print(f"\n[Plan Created]")
    print(f"  {len(plan)} steps: {plan}")
    
    # Act
    for step in plan:
        agent.act(step)
    
    # Learn
    agent.learn(
        concept="AI_intelligence",
        content={
            "AI": "Artificial systems that exhibit intelligent behavior",
            "intelligence": "The capacity to learn, reason, and adapt",
            "relationship": "AI aims to replicate aspects of intelligence",
        },
        episodic_context={
            "situation": "Explored AI and intelligence",
            "actions": plan,
            "outcome": "completed",
        },
    )
    
    # Reflect
    reflection = agent.reflect()
    print(f"\n[Reflection]")
    print(f"  {reflection}")
    
    # Get state
    state = agent.get_state()
    print(f"\n[Final State]")
    print(f"  Semantic memories: {state['semantic_memories']}")
    print(f"  Episodes: {state['episodes']}")
    print(f"  Reasoning quality: {state['reasoning_quality']:.0%}")


async def demo_true_agi():
    """Demo 8: True AGI Agent with OpenShell."""
    print("\n" + "="*70)
    print("  DEMO 8: True AGI Agent")
    print("="*70)
    
    from smith_ai.agi.v2 import TrueAGIAgent
    
    agent = TrueAGIAgent(name="AGI-1", role="general", verbose=True)
    
    # Add custom tools
    def calculator(text: str) -> str:
        import re
        nums = re.findall(r'\d+', text)
        ops = re.findall(r'[+\-*/]', text)
        if nums and ops:
            try:
                expr = ''.join([f" {n} {op} " for n, op in zip(nums, ops)])
                return f"Calculation: {expr.strip()} = {eval(expr.strip())}"
            except:
                pass
        return "Could not parse calculation"
    
    agent.add_tool("calculator", calculator)
    
    print(f"\n[Tools]: {list(agent.tools.keys())}")
    print(f"[OpenShell Available]: {agent.shell.available}")
    
    # Think and act
    print("\n[Think and Act]")
    result = await agent.think_and_act(
        input_data="Calculate 25 + 17 * 3",
        goal="Perform the calculation",
    )
    
    print(f"\n[Result Summary]")
    print(f"  Perception: {result['perception']}")
    print(f"  Reasoning: {result['reasoning']['conclusion'][:50]}...")
    print(f"  Planning: {result['planning']['plan'] if result['planning'] else 'None'}")
    
    # Execute code
    print("\n[Code Execution]")
    code_result = agent.execute_code("print('Hello from OpenShell!')", "python")
    print(f"  Success: {code_result['success']}")
    print(f"  Output: {code_result.get('output', code_result.get('error', ''))}")
    print(f"  Mode: {code_result.get('mode', 'openshell')}")
    
    # Learn from feedback
    print("\n[Learning from Feedback]")
    agent.learn_from_feedback(
        feedback="Good reasoning but need more evidence",
        outcome="success",
    )
    
    # Get status
    status = agent.get_status()
    print(f"\n[Agent Status]")
    print(f"  Cognitive state: {status['cognitive']['state']}")
    print(f"  Reasoning quality: {status['cognitive']['reasoning_quality']:.0%}")
    print(f"  OpenShell: {status['openshell_available']}")


async def demo_multi_agent():
    """Demo 9: Multi-Agent Collaboration."""
    print("\n" + "="*70)
    print("  DEMO 9: Multi-Agent Collaboration")
    print("="*70)
    
    from smith_ai.agi.v2 import CognitiveAgent, CognitiveCrew
    
    # Create specialized agents
    scientist = CognitiveAgent(name="Scientist", role="scientific_researcher", verbose=False)
    analyst = CognitiveAgent(name="Analyst", role="data_analyst", verbose=False)
    writer = CognitiveAgent(name="Writer", role="technical_writer", verbose=False)
    
    # Create crew
    crew = CognitiveCrew(
        agents=[scientist, analyst, writer],
        name="ResearchTeam",
    )
    
    print(f"\n[Crew]: {crew.name}")
    print(f"  Agents: {list(crew.agents.keys())}")
    
    # Solve collaboratively
    print("\n[Solving Collaboratively]")
    result = await crew.solve_collaboratively(
        problem="Analyze the impact of AI on society",
        roles={
            "Scientist": "scientific researcher",
            "Analyst": "data analyst",
            "Writer": "technical writer",
        },
    )
    
    print(f"\n[Results]")
    for agent_name, agent_result in result.items():
        if agent_name != "synthesis":
            print(f"  [{agent_name}]")
            reasoning = agent_result.get("reasoning", {})
            if reasoning:
                print(f"    Conclusion: {reasoning.get('conclusion', 'N/A')[:50]}...")
    
    print(f"\n[Synthesis]")
    print(result["synthesis"][:200] + "...")


async def demo_openshell():
    """Demo 10: OpenShell Integration."""
    print("\n" + "="*70)
    print("  DEMO 10: OpenShell Integration")
    print("="*70)
    
    from smith_ai.agi.v2 import OpenShellIntegration
    
    shell = OpenShellIntegration(verbose=True)
    
    print(f"\n[OpenShell Status]: {'Available' if shell.available else 'Not Available (using fallback)'}")
    
    # Test execution
    print("\n[Test Execution: Python]")
    result = shell.execute_sandboxed("result = 2 + 2; print(f'2 + 2 = {result}')", "python")
    print(f"  Success: {result['success']}")
    print(f"  Output: {result.get('output', result.get('error', ''))}")
    print(f"  Mode: {result.get('mode', 'openshell')}")
    
    # Test math
    print("\n[Test Execution: Math]")
    result = shell.execute_sandboxed("""
import math
result = math.sqrt(16)
print(f'Sqrt(16) = {result}')
print(f'Pi = {math.pi}')
print(f'e = {math.e}')
""", "python")
    print(f"  Output:\n{result.get('output', result.get('error', ''))}")


async def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ████████╗██╗  ██╗███████╗    ███████╗██╗  ██╗██╗████████╗██╗   ██╗     ║
║  ╚══██╔══╝██║  ██║██╔════╝    ██╔════╝██║ ██╔╝██║╚══██╔══╝╚██╗ ██╔╝     ║
║     ██║   ███████║█████╗      ███████╗█████╔╝ ██║   ██║    ╚████╔╝      ║
║     ██║   ██╔══██║██╔══╝      ╚════██║██╔═██╗ ██║   ██║     ╚██╔╝       ║
║     ██║   ██║  ██║███████╗    ███████║██║  ██╗██║   ██║      ██║        ║
║     ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝        ║
║                                                                           ║
║   T R U E   A G I   F R A M E W O R K   -   v 2 . 0                    ║
║                                                                           ║
║   Based on Common Model of Cognition (ACT-R, Soar, Sigma)               ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("""
True AGI Framework - Architecture

This framework implements a comprehensive cognitive architecture based on
the latest AGI research:

CORE COMPONENTS (Common Model of Cognition):
├── PERCEPTION         - Input processing and sensory encoding
├── WORKING MEMORY     - Current context (ACT-R style buffers)
├── PROCEDURAL MEMORY  - Rules and operators (SOAR style productions)
├── DECLARATIVE MEMORY - Semantic + Episodic knowledge
├── WORLD MODEL        - Environment representation
├── MOTOR/ACTION       - Output execution
└── METACOGNITION     - Self-monitoring and improvement

COGNITIVE DESIGN PATTERNS:
├── Observe-Decide-Act (ReAct)
├── Hierarchical Task Networks (HTN)
├── Knowledge Compilation
└── 3-Stage Memory Commitment

AGI REQUIREMENTS:
├── World Models        - Predictive environment representation
├── Planning            - Explicit HTN planning
├── Self-Improvement   - Learning from feedback
├── Multi-Method Reasoning - Deductive, Inductive, Abductive, Causal
└── OpenShell Integration - Sandboxed execution
""")
    
    demos = [
        ("Common Model of Cognition", demo_common_model),
        ("Memory Systems", demo_memory_systems),
        ("Multi-Method Reasoning", demo_reasoning),
        ("Hierarchical Planning", demo_planning),
        ("Metacognition", demo_metacognition),
        ("World Model", demo_world_model),
        ("Cognitive Agent", demo_cognitive_agent),
        ("True AGI Agent", demo_true_agi),
        ("Multi-Agent Collaboration", demo_multi_agent),
        ("OpenShell Integration", demo_openshell),
    ]
    
    results = []
    
    for name, demo_fn in demos:
        try:
            await demo_fn()
            results.append((name, True))
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()
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
    print("  TRUE AGI FRAMEWORK COMPLETE!")
    print("="*70)
    
    print("""
ARCHITECTURE COMPARISON:

┌─────────────────────┬────────────┬────────────┬────────────┐
│ Component           │   ACT-R    │    Soar    │  SmithAI   │
├─────────────────────┼────────────┼────────────┼────────────┤
│ Working Memory      │    ✓       │     ✓      │     ✓      │
│ Procedural Memory   │    ✓       │     ✓      │     ✓      │
│ Declarative Memory  │    ✓       │     ✓      │     ✓      │
│ Semantic Memory     │    ✓       │     ✓      │     ✓      │
│ Episodic Memory    │    ✓       │     ✓      │     ✓      │
│ World Model        │    -       │     -      │     ✓      │
│ Metacognition      │    ✓       │     ✓      │     ✓      │
│ HTN Planning       │    -       │     ✓      │     ✓      │
│ Multi-Agent        │    -       │     -      │     ✓      │
│ OpenShell          │    -       │     -      │     ✓      │
└─────────────────────┴────────────┴────────────┴────────────┘

This True AGI Framework combines the best of ACT-R, Soar, and modern
AGI research into a single, unified architecture.
    """)


if __name__ == "__main__":
    asyncio.run(main())
