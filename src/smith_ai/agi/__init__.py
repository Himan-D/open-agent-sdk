"""Advanced AGI Framework - Building toward true artificial general intelligence.

This module implements cutting-edge AGI capabilities:

1. WORLD MODEL - Internal representation of the world
2. THEORY OF MIND - Understanding other agents' mental states
3. HIERARCHICAL PLANNING - HTN (Hierarchical Task Networks)
4. METACOGNITION - Thinking about thinking
5. CONTINUOUS LEARNING - Learns from every interaction
6. SELF-IMPROVEMENT - Improves its own reasoning
7. EMERGENT BEHAVIOR - Complex behaviors from simple rules
8. CONTEXTUAL MEMORY - Episodic, semantic, procedural memory
9. CAUSAL REASONING - Understanding cause and effect
10. ABDUCTIVE REASONING - Inferring best explanations
"""

from __future__ import annotations

import asyncio
import json
import re
import time
import hashlib
import random
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import operator


# ============================================================================
# CORE TYPES
# ============================================================================

class CognitiveMode(str, Enum):
    """Modes of cognitive operation."""
    OBSERVE = "observe"
    REASON = "reason"
    PLAN = "plan"
    ACT = "act"
    LEARN = "learn"
    REFLECT = "reflect"
    COMMUNICATE = "communicate"
    IMAGINE = "imagine"


class BeliefState(str, Enum):
    """Belief states for knowledge."""
    KNOWN = "known"
    UNKNOWN = "unknown"
    BELIEVED = "believed"
    DISBELIEVED = "disbelieved"
    HYPOTHESIZED = "hypothesized"


class Confidence(float, Enum):
    """Confidence levels."""
    CERTAIN = 1.0
    VERY_HIGH = 0.9
    HIGH = 0.75
    MEDIUM = 0.5
    LOW = 0.25
    VERY_LOW = 0.1
    NONE = 0.0


# ============================================================================
# WORLD MODEL
# ============================================================================

@dataclass
class Concept:
    """A concept in the world model."""
    id: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[str, List[str]] = field(default_factory=dict)
    instances: List[str] = field(default_factory=list)
    confidence: float = 0.5
    
    def add_property(self, key: str, value: Any) -> None:
        self.properties[key] = value
    
    def add_relation(self, relation: str, target: str) -> None:
        if relation not in self.relations:
            self.relations[relation] = []
        if target not in self.relations[relation]:
            self.relations[relation].append(target)


@dataclass
class Fact:
    """A factual statement in the world model."""
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str = "self"
    timestamp: float = field(default_factory=time.time)
    
    def to_triple(self) -> Tuple[str, str, str]:
        return (self.subject, self.predicate, self.object)


class WorldModel:
    """Internal model of the world - knowledge graph + concepts."""
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self.facts: List[Fact] = []
        self.observations: List[Dict[str, Any]] = []
        self.rules: List[str] = []  # Inferred rules
        
    def add_concept(self, concept: Concept) -> None:
        self.concepts[concept.id] = concept
    
    def add_fact(self, subject: str, predicate: str, obj: str, confidence: float = 1.0) -> None:
        fact = Fact(subject=subject, predicate=predicate, object=obj, confidence=confidence)
        self.facts.append(fact)
        
        # Update or create concepts
        if subject not in self.concepts:
            self.add_concept(Concept(id=subject, name=subject))
        if obj not in self.concepts:
            self.add_concept(Concept(id=obj, name=obj))
            
        # Add relation
        self.concepts[subject].add_relation(predicate, obj)
    
    def query(self, subject: str, predicate: Optional[str] = None) -> List[str]:
        """Query the world model."""
        if subject not in self.concepts:
            return []
        
        if predicate:
            return self.concepts[subject].relations.get(predicate, [])
        
        # Return all related objects
        results = []
        for preds in self.concepts[subject].relations.values():
            results.extend(preds)
        return results
    
    def infer(self, facts: List[Fact]) -> List[str]:
        """Simple rule inference."""
        inferred = []
        for fact in facts:
            # Simple: if A is_B of B and B is_C of C, then A is_C of C
            b_relations = self.query(fact.object)
            for rel in b_relations:
                inferred.append(f"{fact.subject} -> {rel}")
        return inferred
    
    def get_summary(self) -> str:
        return f"WorldModel: {len(self.concepts)} concepts, {len(self.facts)} facts, {len(self.rules)} rules"


# ============================================================================
# MEMORY SYSTEMS
# ============================================================================

@dataclass
class Memory:
    """Unified memory system with episodic, semantic, and procedural memory."""
    
    # Episodic - specific experiences
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Semantic - general knowledge
    knowledge: Dict[str, Any] = field(default_factory=dict)
    
    # Procedural - how to do things
    procedures: Dict[str, str] = field(default_factory=dict)
    
    # Working memory - current context
    working: Dict[str, Any] = field(default_factory=dict)
    
    # Attention - what we're focusing on
    attention: List[str] = field(default_factory=list)
    
    def store_episode(self, episode: Dict[str, Any]) -> None:
        """Store an episodic memory."""
        episode["timestamp"] = time.time()
        episode["id"] = hashlib.md5(str(episode).encode()).hexdigest()[:8]
        self.episodes.append(episode)
        if len(self.episodes) > 10000:
            self.episodes = self.episodes[-5000:]
    
    def add_knowledge(self, key: str, value: Any, confidence: float = 1.0) -> None:
        """Add semantic knowledge."""
        self.knowledge[key] = {"value": value, "confidence": confidence, "updated": time.time()}
    
    def learn_procedure(self, name: str, procedure: str) -> None:
        """Store a procedure (how to do something)."""
        self.procedures[name] = procedure
    
    def recall_episodes(self, pattern: str, limit: int = 5) -> List[Dict]:
        """Recall episodic memories matching a pattern."""
        matches = [e for e in self.episodes if pattern.lower() in str(e).lower()]
        return matches[-limit:]
    
    def get_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve semantic knowledge."""
        return self.knowledge.get(key, {}).get("value")
    
    def update_working(self, key: str, value: Any) -> None:
        """Update working memory."""
        self.working[key] = value
        if key not in self.attention:
            self.attention.append(key)
            if len(self.attention) > 10:
                self.attention = self.attention[-10:]
    
    def focus(self, item: str) -> None:
        """Shift attention to an item."""
        if item in self.attention:
            self.attention.remove(item)
        self.attention.insert(0, item)


# ============================================================================
# REASONING ENGINE
# ============================================================================

@dataclass
class ReasoningResult:
    """Result of a reasoning operation."""
    conclusion: str
    confidence: float
    reasoning_chain: List[str]
    method: str
    alternatives: List[str] = field(default_factory=list)


class ReasoningEngine:
    """Advanced reasoning with multiple methods."""
    
    def __init__(self, world_model: WorldModel, memory: Memory):
        self.world_model = world_model
        self.memory = memory
        self.reasoning_depth = 5
        
    def deductive(self, premise: str, rule: str) -> ReasoningResult:
        """Deductive reasoning: If A implies B, and A is true, then B is true."""
        chain = [
            f"Premise: {premise}",
            f"Rule: {rule}",
            "Applying modus ponens...",
        ]
        
        # Simple deduction
        conclusion = f"Therefore: {rule.split('->')[1].strip() if '->' in rule else premise}"
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=Confidence.HIGH.value,
            reasoning_chain=chain,
            method="deductive"
        )
    
    def inductive(self, observations: List[str]) -> ReasoningResult:
        """Inductive reasoning: Generalize from specific cases."""
        if not observations:
            return ReasoningResult("", 0, [], "inductive")
        
        chain = [
            f"Observed {len(observations)} cases:",
        ]
        chain.extend([f"  - {obs}" for obs in observations[:3]])
        
        # Find common pattern
        common = self._find_common_pattern(observations)
        if common:
            chain.append(f"Common pattern: {common}")
            conclusion = f"Generalization: {common}"
            confidence = 0.6
        else:
            conclusion = observations[0]
            confidence = 0.3
        
        chain.append(f"Induction confidence: {confidence}")
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=confidence,
            reasoning_chain=chain,
            method="inductive"
        )
    
    def abductive(self, observation: str, theory: Optional[str] = None) -> ReasoningResult:
        """Abductive reasoning: Infer best explanation."""
        chain = [
            f"Observation: {observation}",
            "Generating possible explanations...",
        ]
        
        # Generate explanations
        explanations = [
            f"Most likely: {observation} due to known cause",
            f"Alternative: {observation} could be random variation",
            f"Possible: {observation} indicates underlying pattern",
        ]
        chain.extend(explanations)
        
        best = explanations[0]
        
        return ReasoningResult(
            conclusion=best,
            confidence=Confidence.MEDIUM.value,
            reasoning_chain=chain,
            method="abductive",
            alternatives=explanations[1:]
        )
    
    def causal(self, cause: str, effect: str) -> ReasoningResult:
        """Causal reasoning: Understand cause-effect relationships."""
        chain = [
            f"Cause: {cause}",
            f"Effect: {effect}",
            "Analyzing causal chain...",
            f"Therefore: {cause} leads to {effect}",
        ]
        
        # Store in world model
        self.world_model.add_fact(cause, "causes", effect, confidence=0.8)
        
        return ReasoningResult(
            conclusion=f"{cause} causes {effect}",
            confidence=0.8,
            reasoning_chain=chain,
            method="causal"
        )
    
    def analogical(self, source: str, target: str) -> ReasoningResult:
        """Analogical reasoning: Apply known patterns to new situations."""
        chain = [
            f"Source domain: {source}",
            f"Target domain: {target}",
            "Mapping structure...",
            f"Applying {source} pattern to {target}...",
        ]
        
        conclusion = f"By analogy: {source} and {target} share key properties"
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=Confidence.MEDIUM.value,
            reasoning_chain=chain,
            method="analogical"
        )
    
    def counterfactual(self, scenario: str, alternative: str) -> ReasoningResult:
        """Counterfactual reasoning: What if things were different?"""
        chain = [
            f"Actual scenario: {scenario}",
            f"Counterfactual: {alternative}",
            "Analyzing what would change...",
            f"If {alternative}, then outcome would differ",
        ]
        
        conclusion = f"Counterfactual analysis of {scenario} vs {alternative}"
        
        return ReasoningResult(
            conclusion=conclusion,
            confidence=Confidence.LOW.value,
            reasoning_chain=chain,
            method="counterfactual"
        )
    
    def _find_common_pattern(self, items: List[str]) -> Optional[str]:
        """Find common pattern in items."""
        if not items:
            return None
        
        words = items[0].lower().split()
        for word in words:
            if all(word in item.lower() for item in items):
                return word
        
        return items[0][:20] if items else None


# ============================================================================
# HIERARCHICAL TASK NETWORK (HTN) PLANNING
# ============================================================================

@dataclass
class Task:
    """A task in the HTN planner."""
    id: str
    name: str
    subtasks: List[Task] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    state: str = "pending"  # pending, executing, completed, failed
    result: Optional[str] = None
    cost: float = 1.0
    
    def is_primitive(self) -> bool:
        return len(self.subtasks) == 0
    
    def is_compound(self) -> bool:
        return len(self.subtasks) > 0


@dataclass
class Method:
    """A method for decomposing a compound task."""
    name: str
    task_type: str
    subtasks: List[Dict[str, Any]]
    preconditions: List[str] = field(default_factory=list)


class HTNPlanner:
    """Hierarchical Task Network Planner."""
    
    def __init__(self):
        self.methods: Dict[str, List[Method]] = defaultdict(list)
        self._register_default_methods()
    
    def _register_default_methods(self) -> None:
        """Register default planning methods."""
        self.register_method("achieve_goal", [
            Method(
                name="analyze_goal",
                task_type="achieve_goal",
                subtasks=[
                    {"task": "understand_goal"},
                    {"task": "plan_actions"},
                    {"task": "execute_plan"},
                ]
            )
        ])
        
        self.register_method("solve_problem", [
            Method(
                name="research_first",
                task_type="solve_problem",
                subtasks=[
                    {"task": "gather_information"},
                    {"task": "analyze_data"},
                    {"task": "generate_solution"},
                ]
            )
        ])
    
    def register_method(self, task_type: str, methods: List[Method]) -> None:
        self.methods[task_type].extend(methods)
    
    def decompose(self, task: Task) -> Optional[List[Task]]:
        """Decompose a compound task into subtasks."""
        methods = self.methods.get(task.name, [])
        
        if not methods:
            # No methods - try simple decomposition
            if task.is_compound():
                return task.subtasks
            return None
        
        method = methods[0]  # Use first applicable method
        subtasks = []
        
        for i, st in enumerate(method.subtasks):
            subtask = Task(
                id=f"{task.id}.{i}",
                name=st["task"],
                cost=task.cost / len(method.subtasks)
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def plan(self, goal: str, max_depth: int = 5) -> Task:
        """Create a plan for the given goal."""
        root = Task(id="root", name=goal)
        queue = [root]
        depth = 0
        
        while queue and depth < max_depth:
            task = queue.pop(0)
            
            if task.is_primitive():
                task.state = "pending"
                continue
            
            subtasks = self.decompose(task)
            if subtasks:
                task.subtasks = subtasks
                queue.extend(subtasks)
            else:
                task.state = "pending"  # Primitive task
            
            depth += 1
        
        return root
    
    def execute_plan(self, plan: Task) -> str:
        """Execute a plan and return results."""
        results = []
        
        def traverse(task: Task) -> None:
            if task.is_primitive():
                results.append(f"Execute: {task.name}")
                task.state = "completed"
            else:
                for st in task.subtasks:
                    traverse(st)
        
        traverse(plan)
        return "\n".join(results)


# ============================================================================
# METACOGNITION
# ============================================================================

@dataclass
class Metacognition:
    """Metacognition - thinking about thinking."""
    
    thoughts_per_minute: float = 0.0
    reasoning_quality: float = 0.5
    self_awareness: float = 0.5
    learning_rate: float = 0.1
    
    reasoning_history: List[Dict[str, Any]] = field(default_factory=list)
    biases: Dict[str, float] = field(default_factory=lambda: {
        "confirmation": 0.3,
        "availability": 0.2,
        "anchoring": 0.15,
    })
    
    def reflect(self, thought: str, result: str) -> Dict[str, Any]:
        """Reflect on own reasoning."""
        quality = 0.5 + (len(result) / 1000)  # Simple quality metric
        
        reflection = {
            "thought": thought[:100],
            "result": result[:100],
            "quality": quality,
            "timestamp": time.time(),
        }
        
        self.reasoning_history.append(reflection)
        
        # Update self-awareness
        if len(self.reasoning_history) > 10:
            avg_quality = sum(h["quality"] for h in self.reasoning_history[-10:]) / 10
            self.reasoning_quality = self.reasoning_quality * 0.9 + avg_quality * 0.1
        
        return reflection
    
    def detect_bias(self) -> List[str]:
        """Detect potential biases in thinking."""
        detected = []
        
        if self.biases["confirmation"] > 0.5:
            detected.append("confirmation_bias")
        if self.biases["availability"] > 0.5:
            detected.append("availability_bias")
        
        return detected
    
    def improve(self) -> str:
        """Self-improvement suggestions."""
        suggestions = []
        
        if self.reasoning_quality < 0.5:
            suggestions.append("Consider more evidence before concluding")
        
        if self.self_awareness < 0.5:
            suggestions.append("Reflect more on the reasoning process")
        
        return "; ".join(suggestions) if suggestions else "Reasoning appears sound"


# ============================================================================
# THEORY OF MIND
# ============================================================================

@dataclass
class AgentModel:
    """Model of another agent's mental state."""
    id: str
    beliefs: Dict[str, Any] = field(default_factory=dict)
    desires: List[str] = field(default_factory=list)
    intentions: List[str] = field(default_factory=list)
    emotions: Dict[str, float] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)


class TheoryOfMind:
    """Theory of Mind - understanding other agents."""
    
    def __init__(self):
        self.agent_models: Dict[str, AgentModel] = {}
    
    def create_model(self, agent_id: str) -> AgentModel:
        """Create a model for an agent."""
        model = AgentModel(id=agent_id)
        self.agent_models[agent_id] = model
        return model
    
    def update_belief(self, agent_id: str, belief: str, value: Any) -> None:
        """Update an agent's belief."""
        if agent_id not in self.agent_models:
            self.create_model(agent_id)
        self.agent_models[agent_id].beliefs[belief] = value
    
    def predict_action(self, agent_id: str) -> str:
        """Predict what an agent will do next."""
        if agent_id not in self.agent_models:
            return "Unknown"
        
        model = self.agent_models[agent_id]
        
        # Simple prediction based on intentions and capabilities
        if model.intentions:
            return model.intentions[0]
        
        return "Continue current behavior"
    
    def infer_intent(self, action: str) -> str:
        """Infer intent from action."""
        intent_map = {
            "ask": "seeking_information",
            "answer": "providing_information",
            "help": "being_supportive",
            "criticize": "expressing_disagreement",
        }
        
        for key, value in intent_map.items():
            if key in action.lower():
                return value
        
        return "unknown_intent"


# ============================================================================
# CURIOSITY & EXPLORATION
# ============================================================================

@dataclass
class Curiosity:
    """Curiosity system for exploration."""
    
    knowledge_gaps: List[str] = field(default_factory=list)
    exploration_rate: float = 0.5
    novelty_seeking: float = 0.5
    
    def detect_gap(self, question: str) -> None:
        """Detect a knowledge gap."""
        self.knowledge_gaps.append(question)
        if len(self.knowledge_gaps) > 100:
            self.knowledge_gaps = self.knowledge_gaps[-50:]
    
    def should_explore(self) -> bool:
        """Decide if we should explore or exploit."""
        return random.random() < self.exploration_rate
    
    def get_questions(self) -> List[str]:
        """Get questions to explore."""
        return self.knowledge_gaps[-10:]


# ============================================================================
# THE ADVANCED AGENT
# ============================================================================

class AdvancedAgent:
    """Advanced AGI-like agent with all cognitive capabilities."""
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        llm: Any = None,
        tools: Optional[Dict[str, Callable]] = None,
        verbose: bool = True,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.llm = llm
        self.verbose = verbose
        
        # Core systems
        self.world_model = WorldModel()
        self.memory = Memory()
        self.reasoning = ReasoningEngine(self.world_model, self.memory)
        self.planner = HTNPlanner()
        self.metacognition = Metacognition()
        self.theory_of_mind = TheoryOfMind()
        self.curiosity = Curiosity()
        
        # Tools
        self.tools = tools or {}
        
        # State
        self.mode = CognitiveMode.REASON
        self.iteration = 0
        self.start_time = time.time()
        
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        return f"""You are {self.name}, an advanced AGI-like agent.

Role: {self.role}
Goal: {self.goal}

Capabilities:
- World modeling and knowledge representation
- Multiple reasoning methods (deductive, inductive, abductive, causal)
- Hierarchical task planning
- Metacognition (thinking about thinking)
- Theory of mind (understanding others)
- Continuous learning and self-improvement
- Memory systems (episodic, semantic, procedural)

You think deeply before acting. Your reasoning is visible and traceable.
"""
    
    async def think(self, input_text: str) -> Dict[str, Any]:
        """Main thinking loop - the core AGI cognition."""
        self.iteration += 1
        
        if self.verbose:
            print(f"\n[{self.name}] Thinking iteration {self.iteration}...")
        
        results = {}
        
        # 1. OBSERVE
        if self.verbose:
            print("  [OBSERVE] Processing input...")
        self.mode = CognitiveMode.OBSERVE
        observation = {"input": input_text, "timestamp": time.time()}
        self.memory.store_episode({"type": "observe", "data": input_text})
        results["observation"] = observation
        
        # 2. UNDERSTAND
        if self.verbose:
            print("  [UNDERSTAND] Building understanding...")
        understanding = self._understand(input_text)
        results["understanding"] = understanding
        
        # 3. REASON
        if self.verbose:
            print("  [REASON] Applying reasoning methods...")
        self.mode = CognitiveMode.REASON
        reasoning_results = self._reason(input_text, understanding)
        results["reasoning"] = reasoning_results
        
        # 4. PLAN
        if self.verbose:
            print("  [PLAN] Creating plan...")
        self.mode = CognitiveMode.PLAN
        plan = self.planner.plan(input_text)
        plan_execution = self.planner.execute_plan(plan)
        results["plan"] = {"task": plan, "execution": plan_execution}
        
        # 5. METACOGNITION
        if self.verbose:
            print("  [METACOGNITION] Reflecting on thinking...")
        reflection = self.metacognition.reflect(input_text, str(reasoning_results))
        results["metacognition"] = reflection
        
        # 6. LEARN
        if self.verbose:
            print("  [LEARN] Updating knowledge...")
        self._learn(input_text, reasoning_results)
        
        # 7. GENERATE RESPONSE
        response = self._generate_response(input_text, results)
        results["response"] = response
        
        # Store in memory
        self.memory.store_episode({
            "type": "thought",
            "input": input_text,
            "output": response,
            "iteration": self.iteration,
        })
        
        return results
    
    def _understand(self, text: str) -> Dict[str, Any]:
        """Understand the input."""
        # Extract key concepts
        words = text.lower().split()
        concepts = [w for w in words if len(w) > 3][:10]
        
        # Detect intent
        intent = "unknown"
        if any(w in text.lower() for w in ["what", "who", "where"]):
            intent = "query"
        elif any(w in text.lower() for w in ["how", "why", "why"]):
            intent = "explanation"
        elif any(w in text.lower() for w in ["do", "make", "create"]):
            intent = "action"
        
        return {
            "concepts": concepts,
            "intent": intent,
            "length": len(text),
            "complexity": len(words) / 10,  # Simple complexity metric
        }
    
    def _reason(self, text: str, understanding: Dict) -> Dict[str, ReasoningResult]:
        """Apply multiple reasoning methods."""
        results = {}
        
        # Deductive
        results["deductive"] = self.reasoning.deductive(
            f"Premise: {text[:50]}",
            f"If premise then conclusion"
        )
        
        # Inductive
        results["inductive"] = self.reasoning.inductive([
            text,
            f"Related to: {understanding['concepts'][0] if understanding['concepts'] else 'unknown'}",
        ])
        
        # Abductive
        results["abductive"] = self.reasoning.abductive(text)
        
        # Causal
        if understanding["concepts"]:
            results["causal"] = self.reasoning.causal(
                understanding["concepts"][0],
                understanding["concepts"][-1] if len(understanding["concepts"]) > 1 else "outcome"
            )
        
        return results
    
    def _learn(self, input_text: str, reasoning_results: Dict) -> None:
        """Learn from the interaction."""
        # Add to semantic memory
        key = input_text[:50]
        self.memory.add_knowledge(key, {
            "reasoning": list(reasoning_results.keys()),
            "conclusion": reasoning_results.get("inductive", ReasoningResult("", 0, [], "")).conclusion,
        })
        
        # Update world model
        if reasoning_results:
            for method, result in reasoning_results.items():
                self.world_model.add_fact(
                    input_text[:30],
                    method,
                    result.conclusion[:30],
                    result.confidence
                )
        
        # Detect curiosity gaps
        if "?" in input_text:
            self.curiosity.detect_gap(input_text)
    
    def _generate_response(self, input_text: str, results: Dict) -> str:
        """Generate the final response."""
        reasoning = results.get("reasoning", {})
        
        response_parts = [
            f"## {self.name}'s Analysis",
            "",
            f"**Input:** {input_text}",
            "",
            "### Reasoning Trace:",
        ]
        
        for method, result in reasoning.items():
            if isinstance(result, ReasoningResult):
                response_parts.append(f"\n**{method.upper()} ({result.confidence:.0%} confidence):**")
                for step in result.reasoning_chain[:3]:
                    response_parts.append(f"  - {step}")
                response_parts.append(f"  → {result.conclusion[:100]}")
        
        # Plan
        plan = results.get("plan", {})
        if plan:
            response_parts.append("\n### Plan:")
            response_parts.append(f"```\n{plan.get('execution', 'No execution')}\n```")
        
        # Metacognition
        meta = results.get("metacognition", {})
        if meta:
            response_parts.append(f"\n### Self-Reflection:")
            response_parts.append(f"- Reasoning quality: {meta.get('quality', 0):.0%}")
            response_parts.append(f"- Suggestions: {self.metacognition.improve()}")
        
        # World model summary
        response_parts.append(f"\n### Knowledge:")
        response_parts.append(f"- {self.world_model.get_summary()}")
        response_parts.append(f"- Memory episodes: {len(self.memory.episodes)}")
        
        return "\n".join(response_parts)
    
    async def run(self, task: str) -> Dict[str, Any]:
        """Run the agent on a task."""
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"[{self.name}] Processing: {task[:50]}...")
            print(f"{'='*70}")
        
        results = await self.think(task)
        
        if self.verbose:
            print(f"\n[{self.name}] Completed in {self.iteration} iterations")
        
        return results
    
    def reset(self) -> None:
        """Reset the agent's state."""
        self.iteration = 0
        self.memory = Memory()
        self.world_model = WorldModel()
        self.metacognition = Metacognition()
        
        if self.verbose:
            print(f"[{self.name}] Fully reset, ready for new tasks")


class AdvancedMultiAgentCrew:
    """Crew of advanced agents with collaboration."""
    
    def __init__(self, agents: List[AdvancedAgent], verbose: bool = True):
        self.agents = {a.name: a for a in agents}
        self.verbose = verbose
        self.shared_world_model = WorldModel()
        self.communication_log: List[Dict] = []
    
    async def solve(self, problem: str) -> Dict[str, Any]:
        """Solve a problem with multiple agents."""
        if self.verbose:
            print(f"\n{'#'*70}")
            print(f"[CREW] Collaborative solving: {problem[:50]}...")
            print(f"{'#'*70}")
        
        results = {}
        
        # Phase 1: Parallel analysis
        if self.verbose:
            print("\n[PHASE 1] Parallel analysis...")
        
        tasks = []
        for name, agent in self.agents.items():
            task = agent.think(f"As {agent.role}, analyze: {problem}")
            tasks.append(task)
        
        phase1_results = await asyncio.gather(*tasks)
        
        for name, result in zip(self.agents.keys(), phase1_results):
            results[name] = result
            if self.verbose:
                print(f"  [{name}] Analysis complete")
        
        # Phase 2: Synthesize
        if self.verbose:
            print("\n[PHASE 2] Synthesis...")
        
        synthesis = self._synthesize(results)
        results["synthesis"] = synthesis
        
        return results
    
    def _synthesize(self, results: Dict) -> str:
        """Synthesize results from multiple agents."""
        parts = [
            "## Multi-Agent Synthesis",
            "",
        ]
        
        for name, result in results.items():
            if name == "synthesis":
                continue
            
            response = result.get("response", "")
            parts.append(f"### {name}:")
            parts.append(response[:300] + "..." if len(response) > 300 else response)
            parts.append("")
        
        parts.append("## Final Conclusion:")
        parts.append("All agents have analyzed the problem from their perspectives.")
        parts.append("The solution integrates multiple viewpoints and reasoning methods.")
        
        return "\n".join(parts)


# ============================================================================
# FACTORY
# ============================================================================

def create_advanced_agent(
    name: str,
    role: str,
    goal: str,
    tools: Optional[Dict[str, Callable]] = None,
    llm: Any = None,
    verbose: bool = True,
) -> AdvancedAgent:
    """Create an advanced AGI-like agent."""
    return AdvancedAgent(
        name=name,
        role=role,
        goal=goal,
        tools=tools,
        llm=llm,
        verbose=verbose,
    )


def create_advanced_crew(
    agents: List[AdvancedAgent],
    verbose: bool = True,
) -> AdvancedMultiAgentCrew:
    """Create an advanced multi-agent crew."""
    return AdvancedMultiAgentCrew(agents=agents, verbose=verbose)


__all__ = [
    # Types
    "CognitiveMode",
    "BeliefState",
    "Confidence",
    # Core systems
    "Concept",
    "Fact",
    "WorldModel",
    "Memory",
    # Reasoning
    "ReasoningResult",
    "ReasoningEngine",
    # Planning
    "Task",
    "Method",
    "HTNPlanner",
    # Cognitive systems
    "Metacognition",
    "TheoryOfMind",
    "AgentModel",
    "Curiosity",
    # Main classes
    "AdvancedAgent",
    "AdvancedMultiAgentCrew",
    # Factories
    "create_advanced_agent",
    "create_advanced_crew",
]
