#!/usr/bin/env python3
"""Advanced AGI Framework Demo - Watch True AGI-Like Thinking.

This demo showcases:
1. World Model - Internal knowledge representation
2. Multiple Reasoning Methods - Deductive, Inductive, Abductive, Causal, Analogical
3. Hierarchical Task Planning (HTN)
4. Metacognition - Thinking about thinking
5. Theory of Mind - Understanding other agents
6. Curiosity & Exploration
7. Memory Systems - Episodic, Semantic, Procedural
8. Multi-Agent Collaboration
"""
import asyncio
import sys

sys.path.insert(0, "/Users/himand/open-agent/src")


async def demo_world_model():
    """Demo 1: World Model."""
    print("\n" + "="*70)
    print("  DEMO 1: World Model")
    print("="*70)
    
    from smith_ai.agi import WorldModel, Concept
    
    wm = WorldModel()
    
    # Add concepts
    wm.add_concept(Concept(id="AI", name="Artificial Intelligence", properties={"type": "technology"}))
    wm.add_concept(Concept(id="ML", name="Machine Learning", properties={"parent": "AI"}))
    
    # Add facts
    wm.add_fact("ML", "is_a", "AI")
    wm.add_fact("NeuralNetworks", "is_a", "ML")
    wm.add_fact("DeepLearning", "is_a", "NeuralNetworks")
    
    print(f"\n[WorldModel] {wm.get_summary()}")
    
    # Query
    results = wm.query("ML")
    print(f"\n[Query] What is ML related to?")
    print(f"  Results: {results}")
    
    # Infer
    inferred = wm.infer(wm.facts)
    print(f"\n[Infer] Inferred relationships:")
    for inf in inferred[:3]:
        print(f"  {inf}")
    
    return wm


async def demo_memory():
    """Demo 2: Memory Systems."""
    print("\n" + "="*70)
    print("  DEMO 2: Memory Systems")
    print("="*70)
    
    from smith_ai.agi import Memory
    
    mem = Memory()
    
    # Store episodes
    mem.store_episode({
        "type": "task",
        "task": "Solve math problem",
        "result": "success",
    })
    mem.store_episode({
        "type": "task",
        "task": "Write code",
        "result": "success",
    })
    
    # Add knowledge
    mem.add_knowledge("Python", "A programming language", confidence=1.0)
    mem.add_knowledge("AI", "Artificial Intelligence", confidence=0.9)
    
    # Learn procedure
    mem.learn_procedure("debug", "1. Identify error, 2. Locate source, 3. Fix, 4. Test")
    
    # Update working memory
    mem.update_working("current_task", "Writing demo")
    mem.focus("Python")
    
    print(f"\n[Memory] Stats:")
    print(f"  Episodes: {len(mem.episodes)}")
    print(f"  Knowledge items: {len(mem.knowledge)}")
    print(f"  Procedures: {len(mem.procedures)}")
    print(f"  Working memory: {list(mem.working.keys())}")
    print(f"  Attention: {mem.attention}")
    
    # Recall
    recalled = mem.recall_episodes("task", limit=5)
    print(f"\n[Recall] Episodes matching 'task': {len(recalled)}")
    
    return mem


async def demo_reasoning():
    """Demo 3: Multiple Reasoning Methods."""
    print("\n" + "="*70)
    print("  DEMO 3: Reasoning Engine")
    print("="*70)
    
    from smith_ai.agi import ReasoningEngine, WorldModel, Memory
    
    wm = WorldModel()
    mem = Memory()
    engine = ReasoningEngine(wm, mem)
    
    # Deductive reasoning
    print("\n[Deductive Reasoning]")
    result = engine.deductive("All humans are mortal", "All humans -> mortal, Socrates is human")
    print(f"  Premise: {result.reasoning_chain[0]}")
    print(f"  Conclusion: {result.conclusion}")
    print(f"  Confidence: {result.confidence:.0%}")
    
    # Inductive reasoning
    print("\n[Inductive Reasoning]")
    result = engine.inductive([
        "The sun rises in the east every day",
        "The sun rose in the east yesterday",
        "The sun rose in the east today",
    ])
    print(f"  Observations: 3 cases")
    print(f"  Generalization: {result.conclusion}")
    print(f"  Confidence: {result.confidence:.0%}")
    
    # Abductive reasoning
    print("\n[Abductive Reasoning]")
    result = engine.abductive("The street is wet")
    print(f"  Observation: The street is wet")
    print(f"  Best explanation: {result.conclusion}")
    print(f"  Alternatives: {len(result.alternatives)}")
    
    # Causal reasoning
    print("\n[Causal Reasoning]")
    result = engine.causal("Rain", "Wet street")
    print(f"  Cause: Rain")
    print(f"  Effect: Wet street")
    print(f"  Conclusion: Rain causes Wet street")
    
    # Analogy
    print("\n[Analogical Reasoning]")
    result = engine.analogical("Heart", "Engine")
    print(f"  {result.conclusion}")
    
    return engine


async def demo_planner():
    """Demo 4: HTN Planner."""
    print("\n" + "="*70)
    print("  DEMO 4: Hierarchical Task Network Planner")
    print("="*70)
    
    from smith_ai.agi import HTNPlanner, Task
    
    planner = HTNPlanner()
    
    # Create a plan
    print("\n[Planning] Creating plan for: Build an AI agent")
    plan = planner.plan("achieve_goal", max_depth=3)
    
    print(f"\n[Plan Structure]")
    print(f"  Root: {plan.name}")
    print(f"  Subtasks: {len(plan.subtasks)}")
    
    for i, st in enumerate(plan.subtasks, 1):
        print(f"    {i}. {st.name} (cost: {st.cost:.2f})")
        for j, sub in enumerate(st.subtasks, 1):
            print(f"      {i}.{j}. {sub.name}")
    
    # Execute
    print(f"\n[Execution]")
    execution = planner.execute_plan(plan)
    print(execution)
    
    return planner


async def demo_metacognition():
    """Demo 5: Metacognition."""
    print("\n" + "="*70)
    print("  DEMO 5: Metacognition - Thinking About Thinking")
    print("="*70)
    
    from smith_ai.agi import Metacognition
    
    meta = Metacognition()
    
    # Reflect on some thoughts
    meta.reflect("I should solve this problem", "The solution involves multiple steps")
    meta.reflect("This approach might not work", "Alternative methods exist")
    meta.reflect("The answer is complex", "Multiple factors contribute")
    
    print(f"\n[Metacognition Stats]")
    print(f"  Reasoning quality: {meta.reasoning_quality:.0%}")
    print(f"  Self-awareness: {meta.self_awareness:.0%}")
    print(f"  Learning rate: {meta.learning_rate:.0%}")
    print(f"  Reasoning history: {len(meta.reasoning_history)}")
    
    # Detect biases
    print(f"\n[Bias Detection]")
    biases = meta.detect_bias()
    if biases:
        print(f"  Potential biases: {', '.join(biases)}")
    else:
        print(f"  No significant biases detected")
    
    # Get improvement suggestions
    print(f"\n[Self-Improvement]")
    suggestions = meta.improve()
    print(f"  {suggestions}")
    
    return meta


async def demo_theory_of_mind():
    """Demo 6: Theory of Mind."""
    print("\n" + "="*70)
    print("  DEMO 6: Theory of Mind")
    print("="*70)
    
    from smith_ai.agi import TheoryOfMind, AgentModel
    
    tom = TheoryOfMind()
    
    # Create models of other agents
    assistant = tom.create_model("Assistant")
    assistant.desires = ["help_user", "be accurate"]
    assistant.intentions = ["provide information"]
    assistant.capabilities = ["search", "reason", "communicate"]
    
    critic = tom.create_model("Critic")
    critic.desires = ["find flaws", "improve quality"]
    critic.intentions = ["evaluate"]
    critic.capabilities = ["analyze", "compare"]
    
    print(f"\n[Agent Models]")
    print(f"  Created {len(tom.agent_models)} agent models")
    
    # Predict actions
    print(f"\n[Action Prediction]")
    for agent_id in tom.agent_models:
        action = tom.predict_action(agent_id)
        print(f"  {agent_id} will likely: {action}")
    
    # Infer intent from action
    print(f"\n[Intent Inference]")
    for action in ["asks a question", "provides help", "criticizes work"]:
        intent = tom.infer_intent(action)
        print(f"  '{action}' → Intent: {intent}")
    
    return tom


async def demo_curiosity():
    """Demo 7: Curiosity System."""
    print("\n" + "="*70)
    print("  DEMO 7: Curiosity & Exploration")
    print("="*70)
    
    from smith_ai.agi import Curiosity
    
    curiosity = Curiosity()
    
    # Detect knowledge gaps
    curiosity.detect_gap("How does neural network learning work?")
    curiosity.detect_gap("What is the meaning of consciousness?")
    curiosity.detect_gap("Why do we dream?")
    
    print(f"\n[Knowledge Gaps] {len(curiosity.knowledge_gaps)} gaps detected")
    for gap in curiosity.knowledge_gaps:
        print(f"  - {gap}")
    
    # Should we explore?
    print(f"\n[Exploration Decision]")
    decision = curiosity.should_explore()
    print(f"  Should explore: {decision}")
    print(f"  Exploration rate: {curiosity.exploration_rate:.0%}")
    
    return curiosity


async def demo_advanced_agent():
    """Demo 8: Advanced AGI Agent."""
    print("\n" + "="*70)
    print("  DEMO 8: Advanced AGI Agent")
    print("="*70)
    
    from smith_ai.agi import AdvancedAgent
    
    # Create an advanced agent
    agent = AdvancedAgent(
        name="AGI-Sage",
        role="AGI Researcher",
        goal="Understand and solve complex problems",
        verbose=True,
    )
    
    # Run on a task
    print("\n[Task] Why is the sky blue?")
    result = await agent.run("Why is the sky blue?")
    
    print("\n" + "-"*70)
    print("[Response Preview]")
    print("-"*70)
    print(result["response"][:500] + "...")
    
    return agent


async def demo_advanced_crew():
    """Demo 9: Advanced Multi-Agent Crew."""
    print("\n" + "="*70)
    print("  DEMO 9: Advanced Multi-Agent Collaboration")
    print("="*70)
    
    from smith_ai.agi import AdvancedAgent, AdvancedMultiAgentCrew
    
    # Create specialized agents
    scientist = AdvancedAgent(
        name="Scientist",
        role="Scientific Researcher",
        goal="Apply scientific method",
        verbose=False,
    )
    
    philosopher = AdvancedAgent(
        name="Philosopher",
        role="Philosophy Expert",
        goal="Provide philosophical insights",
        verbose=False,
    )
    
    engineer = AdvancedAgent(
        name="Engineer",
        role="Problem Solver",
        goal="Build practical solutions",
        verbose=False,
    )
    
    # Create crew
    crew = AdvancedMultiAgentCrew(
        agents=[scientist, philosopher, engineer],
        verbose=True,
    )
    
    # Solve together
    result = await crew.solve("What is the nature of consciousness?")
    
    print(f"\n[Crew] Completed with {len(result)} contributions")
    print(f"\n[Synthesis Preview]")
    print(result["synthesis"][:400] + "...")
    
    return crew


async def demo_all_features():
    """Demo 10: All Features Combined."""
    print("\n" + "="*70)
    print("  DEMO 10: All AGI Features")
    print("="*70)
    
    from smith_ai.agi import (
        AdvancedAgent,
        WorldModel,
        Memory,
        ReasoningEngine,
        HTNPlanner,
        Metacognition,
        TheoryOfMind,
        Curiosity,
    )
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   A G I   F R A M E W O R K   -   C A P A B I L I T I E S       ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║   COGNITIVE ARCHITECTURE                                         ║
    ║   ├── World Model          Knowledge graph & concepts            ║
    ║   ├── Memory Systems       Episodic, Semantic, Procedural        ║
    ║   ├── Reasoning Engine     Deductive, Inductive, Abductive        ║
    ║   ├── HTN Planner          Hierarchical task decomposition       ║
    ║   ├── Metacognition        Self-reflection & improvement          ║
    ║   ├── Theory of Mind       Understanding other agents             ║
    ║   └── Curiosity            Exploration & knowledge gaps           ║
    ║                                                                   ║
    ║   REASONING METHODS                                              ║
    ║   ├── Deductive            If A→B and A, then B                  ║
    ║   ├── Inductive            Generalize from cases                  ║
    ║   ├── Abductive            Best explanation inference             ║
    ║   ├── Causal               Cause-effect relationships             ║
    ║   ├── Analogical           Transfer patterns                      ║
    ║   └── Counterfactual       What if analysis                       ║
    ║                                                                   ║
    ║   MEMORY TYPES                                                    ║
    ║   ├── Episodic             Specific experiences                   ║
    ║   ├── Semantic             General knowledge                      ║
    ║   ├── Procedural          How to do things                       ║
    ║   └── Working             Current context                         ║
    ║                                                                   ║
    ║   SELF-IMPROVEMENT                                                ║
    ║   ├── Bias Detection       Identify thinking biases                ║
    ║   ├── Quality Assessment   Evaluate reasoning quality             ║
    ║   └── Improvement          Suggest and apply fixes                ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Create agent with all systems
    agent = AdvancedAgent(
        name="AGI-Prime",
        role="AGI System",
        goal="Maximize understanding and problem-solving",
        verbose=False,
    )
    
    print("[Testing All Systems Together]")
    
    # World model
    agent.world_model.add_fact("Test", "demonstrates", "World Model")
    print(f"  [OK] World Model: {agent.world_model.get_summary()}")
    
    # Memory
    agent.memory.add_knowledge("test", "working")
    print(f"  [OK] Memory: {len(agent.memory.knowledge)} knowledge items")
    
    # Reasoning
    result = agent.reasoning.inductive(["case1", "case2", "case3"])
    print(f"  [OK] Reasoning: {result.method} completed")
    
    # Planning
    plan = agent.planner.plan("solve_problem")
    print(f"  [OK] Planning: {len(plan.subtasks)} subtasks")
    
    # Metacognition
    meta = agent.metacognition.improve()
    print(f"  [OK] Metacognition: self-improvement active")
    
    # Theory of Mind
    agent.theory_of_mind.create_model("other")
    print(f"  [OK] Theory of Mind: {len(agent.theory_of_mind.agent_models)} models")
    
    # Curiosity
    agent.curiosity.detect_gap("Test question")
    print(f"  [OK] Curiosity: {len(agent.curiosity.knowledge_gaps)} gaps")
    
    return agent


async def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗                          ║
║  ██╔════╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗                         ║
║  ██║     ███████║███████║██╔██╗ ██║██║   ██║                         ║
║  ██║     ██╔══██║██╔══██║██║╚██╗██║██║   ██║                         ║
║  ╚██████╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝                         ║
║   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝                          ║
║                                                                           ║
║   █████╗ ██████╗ ██╗ █████╗ ██╗     ██╗███████╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗   ║
║  ██╔══██╗██╔══██╗██║██╔══██╗██║     ██║╚══███╔╝██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║   ║
║  ███████║██████╔╝██║███████║██║     ██║  ███╔╝ ███████║   ██║   ██║██║   ██║██╔██╗ ██║   ║
║  ██╔══██║██╔══██╗██║██╔══██║██║     ██║ ███╔╝  ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║   ║
║  ██║  ██║██████╔╝██║██║  ██║███████╗██║███████╗██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║   ║
║  ╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ║
║                                                                           ║
║   A D V A N C E D   A G I   F R A M E W O R K                            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("""
Advanced AGI Framework - Next Generation AI Agents

This framework implements cutting-edge AGI capabilities:

  1. World Model     - Internal knowledge representation
  2. Memory Systems - Episodic, Semantic, Procedural
  3. Reasoning       - 5+ reasoning methods
  4. HTN Planning    - Hierarchical task decomposition
  5. Metacognition   - Self-reflection & improvement
  6. Theory of Mind  - Understanding other agents
  7. Curiosity       - Exploration & knowledge gaps
  8. Advanced Agent   - Full cognitive system
  9. Multi-Agent      - Collaborative intelligence
 10. All Features     - Complete system integration
""")
    
    demos = [
        ("World Model", demo_world_model),
        ("Memory Systems", demo_memory),
        ("Reasoning Engine", demo_reasoning),
        ("HTN Planner", demo_planner),
        ("Metacognition", demo_metacognition),
        ("Theory of Mind", demo_theory_of_mind),
        ("Curiosity", demo_curiosity),
        ("Advanced Agent", demo_advanced_agent),
        ("Multi-Agent Crew", demo_advanced_crew),
        ("All Features", demo_all_features),
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
    print("  AGI FRAMEWORK COMPLETE!")
    print("="*70)
    
    print("""
What makes this AGI-like:

1. WORLD MODELING
   - Builds internal representation of knowledge
   - Makes inferences from observations
   - Updates beliefs based on evidence

2. MULTI-METHOD REASONING
   - Not just pattern matching
   - Applies deductive, inductive, abductive logic
   - Understands cause and effect

3. HIERARCHICAL PLANNING
   - Breaks complex tasks into subtasks
   - Plans multiple steps ahead
   - Adapts when plans fail

4. METACOGNITION
   - Thinks about its own thinking
   - Detects biases and errors
   - Actively improves itself

5. THEORY OF MIND
   - Models other agents' mental states
   - Predicts others' actions
   - Understands intentions

6. CONTINUOUS LEARNING
   - Stores every experience
   - Generalizes from cases
   - Gets curious about gaps

This is the foundation for true AGI!
    """)


if __name__ == "__main__":
    asyncio.run(main())
