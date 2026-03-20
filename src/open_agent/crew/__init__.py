"""Autonomous Crew System - CrewAI-style multi-agent orchestration."""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import structlog

from open_agent.agents.runtime import DeepAgent, AgentContext, SoulConfig, Message
from open_agent.agents.tools.base import BaseTool
from open_agent.agents.sandbox.backend import OpenShellBackend

logger = structlog.get_logger(__name__)


class Process(Enum):
    """Execution process types."""
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    PARALLEL = "parallel"


class Agent:
    """Autonomous Agent - similar to CrewAI Agent.
    
    An agent is an autonomous unit that can execute tasks using tools.
    
    Example:
        >>> agent = Agent(
        ...     role="Researcher",
        ...     goal="Find the latest AI news",
        ...     backstory="You are a professional researcher",
        ...     tools=[web_search_tool]
        ... )
    """

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        allow_delegation: bool = True,
        verbose: bool = False,
        max_iterations: int = 15,
        memory_enabled: bool = True,
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.allow_delegation = allow_delegation
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.memory_enabled = memory_enabled
        
        self.soul = SoulConfig(
            name=role,
            responsibilities=[goal],
            work_style=["autonomous", "detail-oriented"],
            custom_instructions=backstory,
        )
        
        system_prompt = self._build_agent_prompt()
        self._agent = DeepAgent(
            name=role,
            system_prompt=system_prompt,
            tools=self.tools,
            soul=self.soul,
            memory_enabled=memory_enabled,
            max_iterations=max_iterations,
        )
        
    def _build_agent_prompt(self) -> str:
        """Build the agent system prompt."""
        return f"""You are a {self.role}.

YOUR GOAL: {self.goal}

BACKSTORY: {self.backstory}

ROLE: You are an expert {self.role} with deep knowledge in your domain.
- Execute your tasks with precision and autonomy
- Use available tools when needed
- Provide clear, actionable outputs
- Think step by step when solving complex problems

OUTPUT FORMAT: Always provide clear, structured responses."""


@dataclass
class Task:
    """Task - A work unit assigned to an agent.
    
    Example:
        >>> task = Task(
        ...     description="Research the latest AI developments",
        ...     agent=researcher_agent,
        ...     expected_output="A summary of 5 key AI developments"
        ... )
    """
    
    description: str
    agent: Optional[Agent] = None
    expected_output: Optional[str] = None
    tools: Optional[List[BaseTool]] = None
    async_execution: bool = False
    context: Optional[List[Task]] = None
    output_file: Optional[str] = None
    
    result: Any = None
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        self.id = f"task_{id(self)}"
        
    def mark_started(self):
        self.status = "in_progress"
        self.started_at = datetime.now()
        
    def mark_completed(self, result: Any):
        self.status = "completed"
        self.result = result
        self.completed_at = datetime.now()
        
    def mark_failed(self, error: str):
        self.status = "failed"
        self.result = error
        self.completed_at = datetime.now()


@dataclass
class Crew:
    """Crew - Orchestrates multiple agents and tasks.
    
    A crew manages the execution of tasks by agents using the specified process.
    
    Example:
        >>> crew = Crew(
        ...     agents=[researcher, writer, coder],
        ...     tasks=[research_task, write_task, code_task],
        ...     process=Process.SEQUENTIAL,
        ...     verbose=True
        ... )
        >>> result = crew.kickoff()
    """
    
    agents: List[Agent] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    process: Process = Process.SEQUENTIAL
    verbose: bool = False
    memory_enabled: bool = True
    max_iterations: int = 15
    
    def __post_init__(self):
        self.id = f"crew_{id(self)}"
        self._task_outputs: Dict[str, Any] = {}
        
    async def _execute_task_async(self, task: Task) -> Any:
        """Execute a single task asynchronously."""
        task.mark_started()
        
        agent = task.agent
        if not agent:
            raise ValueError(f"Task '{task.description}' has no assigned agent")
        
        if self.verbose:
            logger.info(f"[{agent.role}] Starting: {task.description}")
        
        context_prompt = ""
        if task.context:
            context_prompt = "\n## Context from previous tasks:\n"
            for ctx_task in task.context:
                if ctx_task.result:
                    context_prompt += f"- {ctx_task.description}: {ctx_task.result}\n"
        
        full_prompt = f"""## Task: {task.description}

{context_prompt}

## Expected Output: {task.expected_output or 'A comprehensive response'}

Execute this task now and provide your output."""
        
        try:
            await agent._agent.initialize()
            result = await agent._agent.process_message(full_prompt)
            task.mark_completed(result)
            
            if self.verbose:
                logger.info(f"[{agent.role}] Completed: {task.description[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Task failed: {task.description}", error=str(e))
            task.mark_failed(str(e))
            return None

    def _execute_task_sync(self, task: Task) -> Any:
        """Execute a single task synchronously."""
        task.mark_started()
        
        agent = task.agent
        if not agent:
            raise ValueError(f"Task '{task.description}' has no assigned agent")
        
        if self.verbose:
            logger.info(f"[{agent.role}] Starting: {task.description}")
        
        context_prompt = ""
        if task.context:
            context_prompt = "\n## Context from previous tasks:\n"
            for ctx_task in task.context:
                if ctx_task.result:
                    context_prompt += f"- {ctx_task.description}: {ctx_task.result}\n"
        
        full_prompt = f"""## Task: {task.description}

{context_prompt}

## Expected Output: {task.expected_output or 'A comprehensive response'}

Execute this task now and provide your output."""
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(agent._agent.initialize())
            result = loop.run_until_complete(agent._agent.process_message(full_prompt))
            loop.close()
            
            task.mark_completed(result)
            
            if self.verbose:
                logger.info(f"[{agent.role}] Completed: {task.description[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Task failed: {task.description}", error=str(e))
            task.mark_failed(str(e))
            return None

    async def kickoff_async(self) -> Dict[str, Any]:
        """Execute all tasks and return results."""
        if self.verbose:
            logger.info(f"Crew {self.id} starting with {len(self.tasks)} tasks")
        
        if self.process == Process.SEQUENTIAL:
            return await self._execute_sequential_async()
        elif self.process == Process.PARALLEL:
            return await self._execute_parallel_async()
        elif self.process == Process.HIERARCHICAL:
            return await self._execute_hierarchical_async()
        else:
            raise ValueError(f"Unknown process: {self.process}")

    async def _execute_sequential_async(self) -> Dict[str, Any]:
        """Execute tasks sequentially."""
        results = {}
        for i, task in enumerate(self.tasks):
            task.context = self.tasks[:i] if i > 0 else None
            result = await self._execute_task_async(task)
            results[task.description] = result
        return results

    async def _execute_parallel_async(self) -> Dict[str, Any]:
        """Execute independent tasks in parallel."""
        async def run_task(task: Task):
            return task.description, await self._execute_task_async(task)
        
        tasks_with_context = []
        for task in self.tasks:
            task.context = [t for t in self.tasks if t != task]
            tasks_with_context.append(run_task(task))
        
        results_list = await asyncio.gather(*tasks_with_context)
        return dict(results_list)

    async def _execute_hierarchical_async(self) -> Dict[str, Any]:
        """Execute with a manager agent (first agent is manager)."""
        if not self.agents:
            raise ValueError("No agents in crew")
        
        manager = self.agents[0]
        task_assignments = {}
        
        for task in self.tasks:
            task_assignments[task.description] = task.agent.role if task.agent else "unassigned"
        
        assignment_prompt = f"""You are the {manager.role}.
        
Tasks to assign:
{chr(10).join(f"- {desc}: Agent: {assign}" for desc, assign in task_assignments.items())}

Assign each task to the most appropriate agent considering their roles and expertise.
Return a JSON mapping task descriptions to agent roles."""
        
        await manager._agent.initialize()
        assignment_result = await manager._agent.process_message(assignment_prompt)
        
        results = {}
        for task in self.tasks:
            result = await self._execute_task_async(task)
            results[task.description] = result
            
        return results

    def kickoff(self) -> Dict[str, Any]:
        """Synchronous kickoff - runs the crew."""
        if self.verbose:
            logger.info(f"Crew {self.id} kickoff starting")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(self.kickoff_async())
            return results
        finally:
            loop.close()

    async def test_run(self) -> Dict[str, Any]:
        """Run a test with sample tasks."""
        if not self.tasks:
            raise ValueError("No tasks defined")
        
        return await self.kickoff_async()


def create_crew(
    agents: List[Agent],
    tasks: List[Task],
    process: Process = Process.SEQUENTIAL,
    verbose: bool = False,
) -> Crew:
    """Create a configured crew."""
    return Crew(
        agents=agents,
        tasks=tasks,
        process=process,
        verbose=verbose,
    )
