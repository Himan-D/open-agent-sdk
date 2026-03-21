"""Runtime - Execution runtime for agents with tools and context."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from smith_ai.agents import Agent, Task, Crew
from smith_ai.llm import create_llm
from smith_ai.tools import ToolRegistry, register_builtin_tools, get_tool, list_tools


@dataclass
class RuntimeConfig:
    default_provider: str = "openai"
    default_model: Optional[str] = None
    auto_register_tools: bool = True
    verbose: bool = False


class Runtime:
    """Runtime environment for executing agents and crews."""
    
    def __init__(self, config: Optional[RuntimeConfig] = None):
        self.config = config or RuntimeConfig()
        self._agents: Dict[str, Agent] = {}
        self._crews: Dict[str, Crew] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the runtime."""
        if self._initialized:
            return
        
        if self.config.auto_register_tools:
            register_builtin_tools()
        
        self._initialized = True
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent."""
        self._agents[agent.name.lower()] = agent
    
    def register_crew(self, crew: Crew, name: str) -> None:
        """Register a crew."""
        self._crews[name.lower()] = crew
    
    async def run_agent(self, agent_name: str, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Run an agent by name."""
        await self.initialize()
        
        agent = self._agents.get(agent_name.lower())
        if not agent:
            return f"Agent '{agent_name}' not found"
        
        result = await agent.run(task)
        return result.output if result.success else f"Error: {result.error}"
    
    async def run_crew(self, crew_name: str, task: Optional[str] = None) -> str:
        """Run a crew by name."""
        await self.initialize()
        
        crew = self._crews.get(crew_name.lower())
        if not crew:
            return f"Crew '{crew_name}' not found"
        
        result = await crew.kickoff()
        return result.get("final_output", str(result))
    
    async def run_task(self, task: str, tools: Optional[List[str]] = None) -> str:
        """Run a task directly with specified tools."""
        await self.initialize()
        
        tool_objs = []
        if tools:
            for name in tools:
                tool = get_tool(name)
                if tool:
                    tool_objs.append(tool)
        
        agent = Agent(
            name="runtime_agent",
            role="task executor",
            goal=task,
            llm=create_llm(self.config.default_provider, model=self.config.default_model),
            tools=tool_objs,
            verbose=self.config.verbose,
        )
        
        result = await agent.run(task)
        return result.output if result.success else f"Error: {result.error}"
    
    def list_agents(self) -> List[str]:
        return list(self._agents.keys())
    
    def list_crews(self) -> List[str]:
        return list(self._crews.keys())
    
    def list_tools(self) -> List[str]:
        return list_tools()
    
    def status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "agents": len(self._agents),
            "crews": len(self._crews),
            "tools": len(ToolRegistry.get_instance().list_all()),
        }


async def create_runtime(
    provider: str = "openai",
    model: Optional[str] = None,
    tools: Optional[List[str]] = None,
) -> Runtime:
    """Create and initialize a runtime."""
    config = RuntimeConfig(
        default_provider=provider,
        default_model=model,
    )
    runtime = Runtime(config)
    await runtime.initialize()
    return runtime


from smith_ai.core.types import ExecutionResult

__all__ = [
    "Runtime",
    "RuntimeConfig",
    "create_runtime",
]
