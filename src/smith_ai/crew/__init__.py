"""Crew orchestration - Multi-agent coordination."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from smith_ai.agents import Agent, Task, Crew
from smith_ai.core.types import Process


@dataclass
class CrewConfig:
    name: str
    agents: List[Agent]
    tasks: List[Task]
    process: Process = Process.SEQUENTIAL
    verbose: bool = False


class CrewManager:
    """Manage and execute crews."""
    
    def __init__(self):
        self._crews: Dict[str, Crew] = {}
    
    def register(self, crew: Crew, name: str) -> None:
        self._crews[name] = crew
    
    async def execute(self, name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a crew by name."""
        crew = self._crews.get(name)
        if not crew:
            return {"error": f"Crew '{name}' not found"}
        
        result = await crew.kickoff()
        return result
    
    def list_crews(self) -> List[str]:
        return list(self._crews.keys())


class HierarchicalCrew(Crew):
    """Crew with hierarchical execution (manager + workers)."""
    
    def __init__(
        self,
        manager: Agent,
        workers: List[Agent],
        tasks: List[Task],
        verbose: bool = False,
    ):
        self.manager = manager
        self.workers = workers
        self.tasks = tasks
        self.verbose = verbose
        self.results: List[Any] = []
    
    async def kickoff(self) -> Dict[str, Any]:
        """Execute with hierarchical coordination."""
        task_descriptions = [t.description for t in self.tasks]
        
        coordination_prompt = f"""You are the manager coordinating {len(self.workers)} workers to complete {len(self.tasks)} tasks.

Tasks to coordinate:
{chr(10).join(f'{i+1}. {t}' for i, t in enumerate(task_descriptions))}

Workers available: {', '.join(w.name for w in self.workers)}

Coordinate the workers effectively to complete all tasks."""

        if self.verbose:
            print(f"[HierarchicalCrew] Manager: {self.manager.name}")
        
        manager_result = await self.manager.run(coordination_prompt)
        
        worker_results = {}
        for worker in self.workers:
            if self.verbose:
                print(f"[HierarchicalCrew] Worker: {worker.name}")
            worker_task = next((t for t in self.tasks if worker.role.lower() in t.agent_name.lower()), None)
            if worker_task:
                result = await worker.run(worker_task.description)
                worker_results[worker.name] = result.output
        
        return {
            "manager_output": manager_result.output,
            "worker_results": worker_results,
            "final_output": f"Managed by {self.manager.name}. Workers completed: {len(worker_results)}",
        }


class ParallelCrew(Crew):
    """Crew with parallel execution."""
    
    def __init__(self, agents: List[Agent], tasks: List[Task], verbose: bool = False):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose
    
    async def kickoff(self) -> Dict[str, Any]:
        """Execute all tasks in parallel."""
        if self.verbose:
            print(f"[ParallelCrew] Executing {len(self.tasks)} tasks in parallel")
        
        async def run_task(task: Task):
            agent = next((a for a in self.agents if a.name.lower() == task.agent_name.lower()), self.agents[0])
            return await agent.run(task.description)
        
        results = await asyncio.gather(*[run_task(t) for t in self.tasks], return_exceptions=True)
        
        results_dict = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                results_dict[f"task_{i}"] = f"Error: {str(result)}"
            else:
                results_dict[self.tasks[i].agent_name] = result.output if hasattr(result, 'output') else str(result)
        
        return {
            "results": results_dict,
            "final_output": "\n\n".join(str(v) for v in results_dict.values()),
        }


from smith_ai.core.types import Process

__all__ = [
    "CrewConfig",
    "CrewManager",
    "HierarchicalCrew",
    "ParallelCrew",
]
