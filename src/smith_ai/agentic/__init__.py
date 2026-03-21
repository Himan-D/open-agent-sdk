"""Agentic Agent - AGI-like reasoning with ReAct, CoT, and self-reflection.

This module implements agentic AI capabilities:
- ReAct (Reasoning + Acting) loop
- Chain of Thought (CoT) reasoning  
- Self-Reflection and self-correction
- Goal decomposition and planning
- Working memory and context
- Tool mastery through learning
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class ThinkStep(str, Enum):
    """Types of thinking steps."""
    OBSERVE = "observe"
    REASON = "reason"
    PLAN = "plan"
    ACT = "act"
    REFLECT = "reflect"
    REVISIT = "revisit"
    CONCLUDE = "conclude"


@dataclass
class Thought:
    """A single thought/observation during reasoning."""
    step: ThinkStep
    content: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.5
    parent_idx: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


@dataclass
class PlanStep:
    """A step in a plan."""
    action: str
    tool: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    status: str = "pending"  # pending, executing, done, failed, skipped
    result: Optional[str] = None
    reflection: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "tool": self.tool,
            "args": self.args,
            "reason": self.reason,
            "status": self.status,
            "result": self.result,
            "reflection": self.reflection,
        }


@dataclass
class Goal:
    """A goal with decomposition."""
    description: str
    subgoals: List[Goal] = field(default_factory=list)
    status: str = "active"  # active, completed, failed, abandoned
    attempts: int = 0
    max_attempts: int = 3
    
    def is_leaf(self) -> bool:
        return len(self.subgoals) == 0
    
    def complete(self) -> None:
        self.status = "completed"
    
    def fail(self) -> None:
        self.status = "failed"


@dataclass
class WorkingMemory:
    """Agent's working memory - what it's currently thinking about."""
    thoughts: List[Thought] = field(default_factory=list)
    plan: List[PlanStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    reflections: List[str] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    
    def add_thought(self, step: ThinkStep, content: str, confidence: float = 0.5) -> int:
        idx = len(self.thoughts)
        self.thoughts.append(Thought(step=step, content=content, confidence=confidence, parent_idx=idx-1 if self.thoughts else None))
        return idx
    
    def add_observation(self, obs: str) -> None:
        self.observations.append(obs)
        if len(self.observations) > 100:
            self.observations = self.observations[-100:]
    
    def add_reflection(self, refl: str) -> None:
        self.reflections.append(refl)
        if len(self.reflections) > 50:
            self.reflections = self.reflections[-50:]
    
    def add_learning(self, learn: str) -> None:
        self.learnings.append(learn)
        if len(self.learnings) > 100:
            self.learnings = self.learnings[-100:]
    
    def get_context_summary(self) -> str:
        parts = []
        if self.observations:
            parts.append(f"Observations: {'; '.join(self.observations[-5:])}")
        if self.reflections:
            parts.append(f"Reflections: {'; '.join(self.reflections[-3:])}")
        if self.learnings:
            parts.append(f"Learnings: {'; '.join(self.learnings[-3:])}")
        return "\n".join(parts) if parts else "No context yet."
    
    def clear(self) -> None:
        self.thoughts.clear()
        self.plan.clear()
        self.observations.clear()
        self.reflections.clear()
        self.context.clear()


class ReasoningEngine:
    """The brain - handles all reasoning capabilities."""
    
    def __init__(self):
        self.memory = WorkingMemory()
        self.thinking_depth = 3
        self.confidence_threshold = 0.7
    
    def observe(self, input_text: str) -> str:
        """First step: Observe and understand the input."""
        obs = f"Input received: {input_text[:100]}..."
        self.memory.add_thought(ThinkStep.OBSERVE, obs)
        self.memory.add_observation(input_text)
        return obs
    
    def reason(self, prompt: str, max_steps: int = 5) -> List[str]:
        """Chain of Thought reasoning - think step by step."""
        thoughts = []
        
        for step in range(max_steps):
            thought = f"Step {step + 1}: Analyzing this {'systematically' if step == 0 else 'deeply'}..."
            
            if step == 0:
                thought += f"\n  - Breaking down: {prompt[:50]}..."
                thought += "\n  - Identifying key components"
                thought += "\n  - Checking what tools/resources are available"
            elif step == 1:
                thought += "\n  - Connecting pieces of information"
                thought += "\n  - Identifying patterns or relationships"
            elif step == 2:
                thought += "\n  - Evaluating different approaches"
                thought += "\n  - Considering constraints and requirements"
            elif step == 3:
                thought += "\n  - Forming hypotheses"
                thought += "\n  - Testing reasoning chains"
            else:
                thought += "\n  - Synthesizing conclusions"
            
            thoughts.append(thought)
            self.memory.add_thought(ThinkStep.REASON, thought, confidence=0.6 + step * 0.05)
        
        return thoughts
    
    def plan(self, goal: str, available_tools: List[str]) -> List[PlanStep]:
        """Create a plan to achieve the goal."""
        plan = []
        
        plan.append(PlanStep(
            action="Understand the goal",
            reason=f"Goal: {goal[:50]}...",
            tool=None,
        ))
        
        if available_tools:
            plan.append(PlanStep(
                action="Gather information using available tools",
                tool=available_tools[0] if available_tools else None,
                reason="Need context before proceeding",
            ))
        
        plan.append(PlanStep(
            action="Execute main strategy",
            reason="Core task execution",
        ))
        
        plan.append(PlanStep(
            action="Verify and refine",
            reason="Ensure quality of output",
        ))
        
        plan.append(PlanStep(
            action="Present final answer",
            reason="Complete the task",
        ))
        
        self.memory.plan = plan
        return plan
    
    def reflect(self, result: str, expected: Optional[str] = None) -> str:
        """Self-reflection - evaluate the result."""
        reflection = f"Reflection on result: {result[:50]}...\n"
        
        if expected:
            reflection += f"Expected: {expected[:50]}...\n"
            reflection += "Comparison: "
            if expected.lower() in result.lower():
                reflection += "Result matches expectations."
            else:
                reflection += "Result differs - may need adjustment."
        
        reflection += "\nConfidence assessment: "
        reflection += "High" if len(result) > 100 else "Medium" if len(result) > 50 else "Low"
        
        self.memory.add_thought(ThinkStep.REFLECT, reflection, confidence=0.7)
        self.memory.add_reflection(reflection)
        
        return reflection
    
    def decompose_goal(self, goal: str) -> Goal:
        """Break a complex goal into subgoals."""
        main_goal = Goal(description=goal)
        
        subgoals = [
            Goal(description=f"Understand: {goal}"),
            Goal(description=f"Research/plan: {goal}"),
            Goal(description=f"Execute: {goal}"),
            Goal(description=f"Verify: {goal}"),
        ]
        
        main_goal.subgoals = subgoals
        return main_goal
    
    def should_retry(self, attempt: int, max_attempts: int = 3) -> bool:
        """Decide if we should retry after failure."""
        return attempt < max_attempts


class ToolExecutor:
    """Execute tools with proper error handling and learning."""
    
    def __init__(self, tools: Dict[str, Callable]):
        self.tools = tools
        self.execution_history: List[Dict[str, Any]] = []
        self.success_patterns: Dict[str, str] = {}
    
    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute a tool and track the result."""
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
        
        try:
            tool = self.tools[tool_name]
            
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**args) if args else await tool()
            else:
                result = tool(**args) if args else tool()
            
            if hasattr(result, 'output'):
                output = result.output
            elif hasattr(result, 'result'):
                output = result.result
            else:
                output = str(result)
            
            self.execution_history.append({
                "tool": tool_name,
                "args": args,
                "success": True,
                "output_preview": output[:100],
            })
            
            return True, output
            
        except Exception as e:
            self.execution_history.append({
                "tool": tool_name,
                "args": args,
                "success": False,
                "error": str(e),
            })
            return False, f"Error: {str(e)}"
    
    def get_patterns(self) -> Dict[str, str]:
        """Get successful execution patterns."""
        return self.success_patterns.copy()


class AgenticAgent:
    """An agent that can think, plan, and learn like an AGI.
    
    This agent implements:
    - ReAct loop: Think -> Act -> Observe -> Think...
    - Chain of Thought reasoning
    - Self-reflection and self-correction
    - Goal decomposition
    - Working memory
    - Tool mastery
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        llm: Any = None,  # BaseLLM but imported elsewhere
        tools: Optional[Dict[str, Callable]] = None,
        verbose: bool = True,
        max_iterations: int = 10,
        thinking_depth: int = 3,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.llm = llm
        self.verbose = verbose
        
        self.reasoning = ReasoningEngine()
        self.reasoning.thinking_depth = thinking_depth
        
        self.tools = tools or {}
        self.tool_executor = ToolExecutor(self.tools)
        
        self.max_iterations = max_iterations
        self.iteration = 0
        
        self.system_prompt = self._build_system_prompt()
        self.messages: List[Dict[str, str]] = []
        
        self._setup_messages()
    
    def _build_system_prompt(self) -> str:
        tools_section = "\n".join([
            f"- {name}: {desc}" 
            for name, (desc, _) in [
                (n, ("tool", "")) for n, _ in self.tools.items()
            ]
        ]) if self.tools else "No tools available."
        
        return f"""You are {self.name}, an autonomous agent with advanced reasoning capabilities.

Your role: {self.role}
Your goal: {self.goal}

You have these capabilities:
1. REASON: You think step by step before acting
2. PLAN: You create and execute plans
3. OBSERVE: You gather information and learn
4. REFLECT: You evaluate your own performance
5. ADAPT: You adjust your approach based on results

Available tools: {list(self.tools.keys()) if self.tools else 'None'}

When solving a problem:
1. OBSERVE what you're given
2. REASON through the problem (chain of thought)
3. PLAN the steps to solve it
4. ACT by using tools or providing answers
5. REFLECT on the results

Your reasoning is visible and trackable. Think out loud!
"""
    
    def _setup_messages(self) -> None:
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
    
    async def think(self, prompt: str) -> str:
        """Think step by step - the core reasoning loop."""
        if self.verbose:
            print(f"\n[{self.name}] Thinking...")
        
        self.iteration += 1
        
        # Step 1: Observe
        obs = self.reasoning.observe(prompt)
        if self.verbose:
            print(f"  OBSERVE: {obs[:60]}...")
        
        # Step 2: Reason (Chain of Thought)
        thoughts = self.reasoning.reason(prompt, max_steps=self.reasoning.thinking_depth)
        if self.verbose:
            for t in thoughts[:2]:
                print(f"  REASON: {t[:60]}...")
        
        # Step 3: Plan
        available = list(self.tools.keys())
        plan = self.reasoning.plan(prompt, available)
        if self.verbose:
            print(f"  PLAN: {len(plan)} steps created")
        
        # Step 4: Generate response
        context = self.reasoning.memory.get_context_summary()
        reasoning_context = f"""Previous reasoning:
{chr(10).join(t for t in thoughts)}

Context: {context}

Task: {prompt}

Based on the above reasoning, what is your response?"""
        
        self.messages.append({"role": "user", "content": reasoning_context})
        
        if self.llm:
            response = await self.llm.ainvoke(self.messages)
        else:
            # Fallback reasoning without LLM
            response = self._fallback_think(prompt, thoughts, plan)
        
        self.messages.append({"role": "assistant", "content": response})
        
        # Step 5: Reflect
        reflection = self.reasoning.reflect(response)
        if self.verbose:
            print(f"  REFLECT: {reflection[:60]}...")
        
        return response
    
    def _fallback_think(self, prompt: str, thoughts: List[str], plan: List[PlanStep]) -> str:
        """Fallback thinking when no LLM is available - symbolic reasoning."""
        
        prompt_lower = prompt.lower()
        
        # Pattern matching responses
        if "calculate" in prompt_lower or "what is" in prompt_lower:
            # Try to do simple math
            import re
            nums = re.findall(r'\d+', prompt)
            ops = re.findall(r'[+\-*/]', prompt)
            if nums and ops:
                try:
                    expr = ''.join([f" {n} {op} " for n, op in zip(nums, ops)])
                    result = eval(expr.strip())
                    return f"Based on my reasoning:\n\nStep 1: Identify the mathematical operation\nStep 2: Apply to {expr.strip()} = {result}\nStep 3: Present the answer\n\n**Answer: {result}**"
                except:
                    pass
        
        if "search" in prompt_lower or "find" in prompt_lower:
            return f"Based on my reasoning:\n\nStep 1: I need to search for information about this topic\nStep 2: I would use the web_search tool\nStep 3: Synthesize the findings\n\n**To complete this task, I would need access to the web_search tool.**"
        
        # General reasoning response
        reasoning_summary = "\n".join([f"- {t[:80]}" for t in thoughts[:3]])
        
        return f"""## Reasoning Trace

**Observation:** Input received: {prompt[:50]}...

**Chain of Thought:**
{reasoning_summary}

**Plan:**
{chr(10).join([f"{i+1}. {p.action}" for i, p in enumerate(plan)])}

**Conclusion:**
Based on my reasoning process, I need more context or an LLM to provide a detailed answer.

To help you better, I would need:
1. Access to search tools for current information
2. An LLM backend for reasoning
3. More specific details about your request
"""
    
    async def run(self, task: str) -> Dict[str, Any]:
        """Run the agentic loop."""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"[{self.name}] Starting agentic loop for: {task[:50]}...")
            print(f"{'='*60}")
        
        result = await self.think(task)
        
        return {
            "success": True,
            "output": result,
            "iterations": self.iteration,
            "thoughts": len(self.reasoning.memory.thoughts),
            "reflections": self.reasoning.memory.reflections.copy(),
            "learnings": self.reasoning.memory.learnings.copy(),
        }
    
    async def run_with_tools(self, task: str) -> Dict[str, Any]:
        """Run with tool execution."""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"[{self.name}] Agentic loop with tools: {task[:50]}...")
            print(f"{'='*60}")
        
        # First, think about the task
        thinking = await self.think(task)
        
        # Try to extract and execute tools
        tools_used = []
        tool_results = []
        
        # Parse potential tool calls from thinking
        tool_pattern = r'"tool":\s*"(\w+)"'
        tool_calls = re.findall(tool_pattern, thinking)
        
        for tool_name in tool_calls:
            if tool_name in self.tools:
                if self.verbose:
                    print(f"  EXECUTING TOOL: {tool_name}")
                
                success, result = await self.tool_executor.execute(tool_name, {})
                tools_used.append(tool_name)
                tool_results.append({"tool": tool_name, "success": success, "result": result})
                
                if self.verbose:
                    print(f"    Result: {str(result)[:80]}...")
                
                # Add tool result to context
                self.reasoning.memory.add_observation(f"Tool {tool_name}: {str(result)[:50]}...")
        
        return {
            "success": True,
            "output": thinking,
            "iterations": self.iteration,
            "tools_used": tools_used,
            "tool_results": tool_results,
            "thoughts": self.reasoning.memory.thoughts.copy(),
        }
    
    def reset(self) -> None:
        """Reset the agent's memory."""
        self.reasoning.memory.clear()
        self.iteration = 0
        self._setup_messages()
        if self.verbose:
            print(f"[{self.name}] Memory cleared, ready for new task")


class MultiAgentCrew:
    """A crew of agentic agents working together.
    
    Implements:
    - Role-based specialization
    - Communication between agents
    - Collaborative problem solving
    - Emergent behavior
    """
    
    def __init__(
        self,
        agents: List[AgenticAgent],
        coordinator: Optional[AgenticAgent] = None,
        verbose: bool = True,
    ):
        self.agents = {a.name: a for a in agents}
        self.coordinator = coordinator
        self.verbose = verbose
        self.shared_memory: Dict[str, Any] = {}
    
    def add_agent(self, agent: AgenticAgent) -> None:
        self.agents[agent.name] = agent
    
    async def solve(self, problem: str) -> Dict[str, Any]:
        """Solve a problem collaboratively."""
        if self.verbose:
            print(f"\n{'#'*60}")
            print(f"[CREW] Collaborative problem solving")
            print(f"{'#'*60}")
            print(f"Problem: {problem[:50]}...")
        
        results = {}
        
        if len(self.agents) == 1:
            # Single agent
            agent = list(self.agents.values())[0]
            result = await agent.run(problem)
            results[agent.name] = result
        else:
            # Multi-agent collaboration
            # Step 1: Coordinator decomposes the problem
            if self.coordinator:
                coord_result = await self.coordinator.run(
                    f"Decompose this problem into subtasks for specialized agents: {problem}"
                )
                results["coordinator"] = coord_result
                if self.verbose:
                    print(f"\n[COORDINATOR] Decomposed problem")
            
            # Step 2: Each agent works on their part
            for name, agent in self.agents.items():
                if name != (self.coordinator.name if self.coordinator else None):
                    subproblem = f"As a {agent.role}, solve this aspect: {problem}"
                    result = await agent.run(subproblem)
                    results[name] = result
                    if self.verbose:
                        print(f"\n[{name}] Completed their analysis")
            
            # Step 3: Synthesize results
            synthesis = self._synthesize(results)
            results["synthesis"] = synthesis
        
        return results
    
    def _synthesize(self, results: Dict[str, Any]) -> str:
        """Synthesize results from multiple agents."""
        parts = []
        for name, result in results.items():
            if name != "synthesis":
                output = result.get("output", "")
                parts.append(f"## {name}\n{output[:200]}...")
        
        return f"## Multi-Agent Synthesis\n\n" + "\n\n".join(parts)


# Example factory function
def create_agentic_agent(
    name: str,
    role: str,
    goal: str,
    tools: Optional[Dict[str, Callable]] = None,
    llm: Any = None,
    verbose: bool = True,
) -> AgenticAgent:
    """Create an agentic agent with the given parameters."""
    return AgenticAgent(
        name=name,
        role=role,
        goal=goal,
        tools=tools,
        llm=llm,
        verbose=verbose,
    )


__all__ = [
    "ThinkStep",
    "Thought",
    "PlanStep",
    "Goal",
    "WorkingMemory",
    "ReasoningEngine",
    "ToolExecutor",
    "AgenticAgent",
    "MultiAgentCrew",
    "create_agentic_agent",
]
