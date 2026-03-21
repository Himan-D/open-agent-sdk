"""Agent System - Core agent implementation with tool support."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from smith_ai.core.types import (
    BaseLLM,
    BaseTool,
    BaseAgent,
    AgentConfig,
    AgentMessage,
    ExecutionResult,
    LLMConfig,
    LLMProvider,
    Process,
    ToolResult,
)
from smith_ai.llm import create_llm, LLMRegistry
from smith_ai.tools import ToolRegistry, get_tool


@dataclass
class Task:
    description: str
    agent_name: str
    expected_output: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "agent_name": self.agent_name,
            "expected_output": self.expected_output,
        }


class Agent(BaseAgent):
    """AI Agent with LLM and tool support."""
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str = "",
        llm: Optional[BaseLLM] = None,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[List[BaseTool]] = None,
        verbose: bool = False,
        max_iterations: int = 10,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory or f"You are {name}, a {role}."
        
        if llm:
            self.llm = llm
        elif llm_config:
            self.llm = LLMRegistry.create(llm_config)
        else:
            self.llm = None
        
        self.tools = tools or []
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.messages: List[Dict[str, str]] = []
        self._setup_system_prompt()
    
    def _setup_system_prompt(self) -> None:
        tool_descriptions = []
        for t in self.tools:
            tool_descriptions.append(f"- {t.name}: {t.description}")
        
        tools_section = "\n".join(tool_descriptions) if tool_descriptions else "No tools available."
        
        self.system_prompt = f"""{self.backstory}

Your goal: {self.goal}

Available tools:
{tools_section}

Instructions:
- Use tools when needed to accomplish the task
- If you need to use a tool, respond in this format:
{{"tool": "tool_name", "arguments": {{"arg1": "value1"}}}}
- If you have a final answer, respond in this format:
{{"response": "your answer here"}}
"""
        self.messages = [{"role": "system", "content": self.system_prompt}]
    
    def add_tool(self, tool: BaseTool) -> None:
        self.tools.append(tool)
        self._setup_system_prompt()
    
    async def run(self, task: str) -> ExecutionResult:
        """Run a task with the agent."""
        if not self.llm:
            return ExecutionResult(success=False, error="No LLM configured")
        
        self.messages.append({"role": "user", "content": task})
        
        for iteration in range(self.max_iterations):
            try:
                response = await self.llm.ainvoke(self.messages)
                
                if self.verbose:
                    print(f"[{self.name}] Iteration {iteration + 1}: {response[:100]}...")
                
                tool_match = re.search(r'"tool":\s*"(\w+)"', response)
                response_match = re.search(r'"response":\s*"([^"]+)"', response)
                
                if tool_match:
                    tool_name = tool_match.group(1)
                    tool = get_tool(tool_name) or next((t for t in self.tools if t.name == tool_name), None)
                    
                    if tool:
                        args_match = re.search(r'"arguments":\s*(\{[^}]+\})', response)
                        args = {}
                        if args_match:
                            try:
                                args = json.loads(args_match.group(1))
                            except:
                                pass
                        
                        result = await tool.execute(**args)
                        self.messages.append({"role": "tool", "content": str(result)})
                    else:
                        self.messages.append({"role": "assistant", "content": f"Tool '{tool_name}' not found"})
                        break
                
                elif response_match:
                    final_response = response_match.group(1)
                    return ExecutionResult(success=True, output=final_response)
                
                else:
                    return ExecutionResult(success=True, output=response)
                    
            except Exception as e:
                return ExecutionResult(success=False, error=str(e))
        
        return ExecutionResult(success=False, error=f"Max iterations ({self.max_iterations}) reached")
    
    async def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]
    
    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages.copy()


class Crew:
    """Multi-agent crew orchestration."""
    
    def __init__(
        self,
        agents: List[Agent],
        tasks: Optional[List[Task]] = None,
        process: Process = Process.SEQUENTIAL,
        verbose: bool = False,
    ):
        self.agents = agents
        self.tasks = tasks or []
        self.process = process
        self.verbose = verbose
        self.results: List[ExecutionResult] = []
    
    async def kickoff(self) -> Dict[str, Any]:
        """Execute all tasks in the crew."""
        if self.process == Process.SEQUENTIAL:
            return await self._run_sequential()
        elif self.process == Process.PARALLEL:
            return await self._run_parallel()
        elif self.process == Process.HIERARCHICAL:
            return await self._run_hierarchical()
        return {"error": "Unknown process type"}
    
    async def _run_sequential(self) -> Dict[str, Any]:
        results = {}
        for i, task in enumerate(self.tasks):
            agent = next((a for a in self.agents if a.name.lower() == task.agent_name.lower()), self.agents[0])
            
            if self.verbose:
                print(f"[Crew] Running task {i+1}: {task.description} with {agent.name}")
            
            result = await agent.run(task.description)
            results[task.agent_name] = result.output
            
            if task.expected_output:
                result = await agent.run(f"Based on: {result.output}\n\n{task.expected_output}")
                results[f"{task.agent_name}_final"] = result.output
        
        self.results = [r for r in results.values() if hasattr(r, 'success')]
        return {"results": results, "final_output": "\n\n".join(str(v) for v in results.values())}
    
    async def _run_parallel(self) -> Dict[str, Any]:
        async def run_task(task: Task):
            agent = next((a for a in self.agents if a.name.lower() == task.agent_name.lower()), self.agents[0])
            return await agent.run(task.description)
        
        results_list = await asyncio.gather(*[run_task(t) for t in self.tasks])
        results = {t.agent_name: r.output for t, r in zip(self.tasks, results_list)}
        return {"results": results, "final_output": "\n\n".join(str(v) for v in results.values())}
    
    async def _run_hierarchical(self) -> Dict[str, Any]:
        if not self.agents:
            return {"error": "No agents"}
        
        manager = self.agents[0]
        subtasks = [t.description for t in self.tasks]
        
        if self.verbose:
            print(f"[Crew] Manager {manager.name} coordinating {len(subtasks)} tasks")
        
        coordination_prompt = f"""You are the manager coordinating the following tasks:
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(subtasks))}

Coordinate your team to complete all tasks efficiently."""
        
        result = await manager.run(coordination_prompt)
        return {"manager_output": result.output, "tasks": subtasks}


class AgentExecutor:
    """Execute agent tasks with proper lifecycle management."""
    
    def __init__(self, agent: Agent):
        self.agent = agent
        self._running = False
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Execute a task with optional context."""
        self._running = True
        try:
            if context:
                context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
                task = f"Context:\n{context_str}\n\nTask: {task}"
            
            return await self.agent.run(task)
        finally:
            self._running = False
    
    async def execute_stream(self, task: str):
        """Stream agent responses."""
        result = await self.execute(task)
        yield result.output


def create_agent(
    name: str,
    role: str,
    goal: str,
    provider: str = "openai",
    model: Optional[str] = None,
    tools: Optional[List[str]] = None,
    verbose: bool = False,
) -> Agent:
    """Factory function to create an agent."""
    llm = create_llm(provider, model=model)
    
    tool_objs = []
    if tools:
        for tool_name in tools:
            tool = get_tool(tool_name)
            if tool:
                tool_objs.append(tool)
    
    return Agent(
        name=name,
        role=role,
        goal=goal,
        llm=llm,
        tools=tool_objs,
        verbose=verbose,
    )


def create_crew(
    agents: List[Dict[str, Any]],
    tasks: List[Dict[str, str]],
    process: str = "sequential",
) -> Crew:
    """Factory function to create a crew."""
    agent_objs = []
    
    for agent_def in agents:
        agent = create_agent(**agent_def)
        agent_objs.append(agent)
    
    task_objs = [Task(**t) for t in tasks]
    
    return Crew(
        agents=agent_objs,
        tasks=task_objs,
        process=Process(process),
    )


from smith_ai.core.types import BaseLLM, AgentConfig, ExecutionResult, LLMConfig, Process, BaseTool

__all__ = [
    "Agent",
    "Task",
    "Crew",
    "Process",
    "AgentExecutor",
    "create_agent",
    "create_crew",
]
