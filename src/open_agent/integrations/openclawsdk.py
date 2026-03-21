"""OpenShell & OpenClaw Integration - Full sandbox + orchestration.

This module provides complete integration with:
- OpenShell: Isolated sandbox execution (Docker/K3s containers)
- OpenClaw: Multi-agent orchestration with skills, memory, delegation
- Policy enforcement for secure execution
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# OPENSHELL SANDBOX INTEGRATION
# =============================================================================

class SandboxType(str, Enum):
    """Sandbox environment types."""
    DOCKER = "docker"
    K3S = "k3s"
    NATIVE = "native"
    AUTO = "auto"


@dataclass
class SandboxConfig:
    """Configuration for sandbox."""
    sandbox_type: SandboxType = SandboxType.DOCKER
    policy_file: Optional[str] = None
    credential_provider: str = "nvidia"
    root_dir: Optional[str] = None
    timeout: int = 300


class SandboxSession:
    """OpenShell sandbox session - isolated execution environment."""
    
    def __init__(self, session_id: str, backend: "OpenShellBackend"):
        self.session_id = session_id
        self.backend = backend
        self._active = True
    
    def exec(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in sandbox."""
        return self.backend._exec(self.session_id, command, timeout)
    
    def write(self, path: str, content: str) -> Dict[str, Any]:
        """Write file to sandbox."""
        return self.backend._write(self.session_id, path, content)
    
    def read(self, path: str) -> str:
        """Read file from sandbox."""
        return self.backend._read(self.session_id, path)
    
    def install(self, package: str) -> Dict[str, Any]:
        """Install package in sandbox."""
        return self.exec(f"pip install {package}")
    
    def git_clone(self, repo: str, path: str = ".") -> Dict[str, Any]:
        """Clone git repository."""
        return self.exec(f"git clone {repo} {path}")
    
    def run_python(self, code: str) -> Dict[str, Any]:
        """Run Python code in sandbox."""
        return self.exec(f'python3 -c "{code}"')
    
    def run_shell(self, script: str) -> Dict[str, Any]:
        """Run shell script."""
        return self.exec(f"bash -c '{script}'")
    
    def terminate(self):
        """Terminate sandbox session."""
        if self._active:
            self.backend._terminate(self.session_id)
            self._active = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.terminate()


class OpenShellBackend:
    """NVIDIA OpenShell sandbox backend - full integration.
    
    OpenShell provides:
    - Kernel-level isolation (Landlock LSM)
    - Policy-enforced file/network access
    - Credential injection
    - Privacy routing for inference
    
    CLI Reference:
        openshell sandbox create [--from <agent>]  - Create sandbox
        openshell sandbox list                       - List sandboxes
        openshell sandbox get <name>                 - Get sandbox info
        openshell sandbox delete <name>              - Delete sandbox
        openshell sandbox upload <name> <src> <dst>  - Upload files
        openshell sandbox download <name> <src> <dst> - Download files
        openshell exec <name> <command>              - Execute in sandbox
        openshell logs <name>                        - View logs
        openshell term                               - Terminal UI
    """
    
    OPENSHELL_PATH = os.path.expanduser("~/.local/bin/openshell")
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._sessions: Dict[str, SandboxSession] = {}
        self._openshell_path = self._find_openshell()
        self._openshell_available = self._openshell_path is not None
        if self._openshell_available:
            logger.info("openshell_found", path=self._openshell_path)
        else:
            logger.warning("openshell_not_found")
    
    def _find_openshell(self) -> Optional[str]:
        """Find OpenShell CLI binary."""
        import shutil
        paths = [
            self.OPENSHELL_PATH,
            os.path.expanduser("~/.cargo/bin/openshell"),
            shutil.which("openshell"),
        ]
        for path in paths:
            if path and os.path.isfile(path):
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
                    if result.returncode == 0:
                        return path
                except:
                    pass
        return None
    
    @property
    def version(self) -> Optional[str]:
        """Get OpenShell version."""
        if not self._openshell_path:
            return None
        try:
            result = subprocess.run(
                [self._openshell_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _run(self, args: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run openshell command."""
        return subprocess.run(
            [self._openshell_path] + args,
            capture_output=True, text=True, timeout=timeout
        )
    
    def create_sandbox(
        self,
        name: Optional[str] = None,
        agent: Optional[str] = None,
        from_image: Optional[str] = None,
        policy_file: Optional[str] = None,
        forward_port: Optional[int] = None,
    ) -> SandboxSession:
        """Create new sandbox session.
        
        Args:
            name: Sandbox name (auto-generated if not provided)
            agent: Agent to launch in sandbox (claude, opencode, codex, copilot)
            from_image: Community sandbox image to use
            policy_file: Path to YAML policy file
            forward_port: Local port to forward to sandbox
            
        Returns:
            SandboxSession for the created sandbox
        """
        session_id = name or f"sandbox_{uuid.uuid4().hex[:8]}"
        
        if self._openshell_available:
            try:
                cmd = ["sandbox", "create"]
                if name:
                    cmd.extend(["--name", name])
                if agent:
                    cmd.extend(["--", agent])
                if from_image:
                    cmd.extend(["--from", from_image])
                if policy_file:
                    cmd.extend(["--policy", policy_file])
                if forward_port:
                    cmd.extend(["--forward", str(forward_port)])
                
                result = self._run(cmd, timeout=120)
                if result.returncode == 0:
                    logger.info("openshell_sandbox_created", session_id=session_id, output=result.stdout)
                else:
                    logger.warning("openshell_create_failed", stderr=result.stderr)
            except Exception as e:
                logger.warning("openshell_create_error", error=str(e))
        
        session = SandboxSession(session_id, self)
        self._sessions[session_id] = session
        return session
    
    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all sandboxes."""
        if not self._openshell_available:
            return []
        
        try:
            result = self._run(["sandbox", "list", "--format", "json"], timeout=30)
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
        except Exception as e:
            logger.warning("openshell_list_error", error=str(e))
        
        return []
    
    def get_sandbox(self, name: str) -> Optional[Dict[str, Any]]:
        """Get sandbox details."""
        if not self._openshell_available:
            return None
        
        try:
            result = self._run(["sandbox", "get", name], timeout=30)
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
        except:
            pass
        
        return None
    
    def delete_sandbox(self, name: str) -> bool:
        """Delete a sandbox."""
        if not self._openshell_available:
            return False
        
        try:
            result = self._run(["sandbox", "delete", name], timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def _exec(self, session_id: str, command: str, timeout: int) -> Dict[str, Any]:
        """Execute command in sandbox."""
        if self._openshell_available:
            try:
                result = subprocess.run(
                    [self._openshell_path, "exec", session_id, "--", command],
                    capture_output=True, text=True, timeout=timeout
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                    "mode": "openshell",
                }
            except Exception as e:
                logger.warning("openshell_exec_error", error=str(e))
        
        # Fallback to local execution
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "mode": "local",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "mode": "local"}
    
    def _write(self, session_id: str, path: str, content: str) -> Dict[str, Any]:
        """Write file to sandbox using upload."""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=os.path.basename(path)) as f:
                f.write(content)
                temp_path = f.name
            
            if self._openshell_available:
                try:
                    result = subprocess.run(
                        [self._openshell_path, "sandbox", "upload", session_id, temp_path, path],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        return {"success": True, "path": path, "mode": "openshell"}
                except Exception as e:
                    logger.warning("openshell_upload_error", error=str(e))
            
            # Fallback - write locally
            import shutil
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            shutil.copy(temp_path, path)
            return {"success": True, "path": path, "mode": "local"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _read(self, session_id: str, path: str) -> str:
        """Read file from sandbox using download."""
        if self._openshell_available:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    temp_path = f.name
                
                result = subprocess.run(
                    [self._openshell_path, "sandbox", "download", session_id, path, temp_path],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    with open(temp_path, 'r') as f:
                        return f.read()
            except Exception as e:
                logger.warning("openshell_download_error", error=str(e))
        
        # Fallback - read locally
        try:
            with open(path, 'r') as f:
                return f.read()
        except:
            return ""
    
    def _terminate(self, session_id: str):
        """Terminate/delete sandbox session."""
        if self._openshell_available:
            try:
                self._run(["sandbox", "delete", session_id], timeout=30)
            except:
                pass
        
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def logs(self, session_id: str, tail: int = 100) -> str:
        """Get sandbox logs."""
        if not self._openshell_available:
            return ""
        
        try:
            result = subprocess.run(
                [self._openshell_path, "logs", session_id, "--tail", str(tail)],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout
        except:
            return ""
    
    def set_policy(self, session_id: str, policy_path: str) -> bool:
        """Set sandbox policy from YAML file."""
        if not self._openshell_available:
            return False
        
        try:
            result = self._run(["policy", "set", "--policy", policy_path, session_id], timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def get_policy(self, session_id: str) -> Optional[str]:
        """Get current sandbox policy."""
        if not self._openshell_available:
            return None
        
        try:
            result = self._run(["policy", "get", session_id], timeout=30)
            if result.returncode == 0:
                return result.stdout
        except:
            pass
        return None
    
    def list_sessions(self) -> List[str]:
        """List active session IDs."""
        return list(self._sessions.keys())
    
    def cleanup(self):
        """Clean up all sessions."""
        for session_id in list(self._sessions.keys()):
            self._terminate(session_id)


# =============================================================================
# OPENCLAW ORCHESTRATION INTEGRATION
# =============================================================================

@dataclass
class Skill:
    """OpenClaw-style skill."""
    name: str
    description: str
    instructions: str
    file_path: Optional[str] = None
    
    @classmethod
    def from_file(cls, path: str) -> "Skill":
        """Load skill from markdown file."""
        with open(path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        name = lines[0].replace('#', '').strip()
        description = ""
        instructions = content
        
        return cls(name=name, description=description, instructions=instructions, file_path=path)


@dataclass 
class SoulConfig:
    """OpenClaw SOUL.md - Agent personality configuration."""
    name: str
    emoji: str = "🤖"
    team: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    reporting_to: Optional[str] = None
    work_style: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    custom_instructions: str = ""
    
    def to_system_prompt(self) -> str:
        """Generate system prompt from soul config."""
        parts = [f"You are {self.name} {self.emoji}."]
        
        if self.team:
            parts.append(f"Team: {self.team}")
        
        if self.responsibilities:
            parts.append(f"Responsibilities: {', '.join(self.responsibilities)}")
        
        if self.work_style:
            parts.append(f"Work style: {', '.join(self.work_style)}")
        
        if self.constraints:
            parts.append(f"Constraints: {', '.join(self.constraints)}")
        
        if self.custom_instructions:
            parts.append(f"\n{self.custom_instructions}")
        
        return "\n".join(parts)


@dataclass
class Channel:
    """OpenClaw channel - communication endpoint."""
    name: str
    type: str  # slack, discord, whatsapp, terminal, api
    config: Dict[str, Any] = field(default_factory=dict)


class OpenClawAgent:
    """OpenClaw-style agent with full orchestration.
    
    Features from OpenClaw:
    - SOUL.md personality
    - Skills system
    - Memory integration
    - Multi-channel support
    - Planning and reasoning
    """
    
    def __init__(
        self,
        name: str,
        soul: SoulConfig,
        llm: Any = None,
        skills: Optional[List[Skill]] = None,
        sandbox: Optional[OpenShellBackend] = None,
        memory: bool = True,
    ):
        self.name = name
        self.soul = soul
        self.llm = llm
        self.skills = skills or []
        self.sandbox = sandbox
        self.memory = memory
        self._history: List[Dict[str, str]] = []
        self._tools: Dict[str, Any] = {}
    
    def add_skill(self, skill: Skill):
        """Add a skill to the agent."""
        self.skills.append(skill)
    
    def use_sandbox(self, command: str) -> Dict[str, Any]:
        """Execute command in sandbox."""
        if not self.sandbox:
            self.sandbox = OpenShellBackend()
        
        session = self.sandbox.create_sandbox(self.name)
        result = session.exec(command)
        session.terminate()
        return result
    
    async def think(self, prompt: str) -> str:
        """Process prompt through LLM."""
        if not self.llm:
            raise ValueError("No LLM configured")
        
        messages = [
            {"role": "system", "content": self.soul.to_system_prompt()},
            *self._history,
            {"role": "user", "content": prompt},
        ]
        
        response = await self.llm.ainvoke(messages)
        
        self._history.append({"role": "user", "content": prompt})
        self._history.append({"role": "assistant", "content": response})
        
        return response
    
    async def execute(self, task: str) -> str:
        """Execute task with planning."""
        plan = await self._plan(task)
        result = await self._execute_plan(plan)
        return result
    
    async def _plan(self, task: str) -> List[str]:
        """Break task into steps."""
        if not self.llm:
            return [task]
        
        response = await self.llm.ainvoke([
            {"role": "system", "content": "Break this task into numbered steps."},
            {"role": "user", "content": task},
        ])
        
        steps = [s.strip() for s in response.split('\n') if s.strip()]
        return steps or [task]
    
    async def _execute_plan(self, steps: List[str]) -> str:
        """Execute plan steps."""
        results = []
        for step in steps:
            result = await self.think(step)
            results.append(result)
        return "\n".join(results)
    
    def delegate(self, task: str, to: "OpenClawAgent") -> str:
        """Delegate task to another agent."""
        return f"[Delegated to {to.name}]: {task}"


class OpenClawCrew:
    """OpenClaw-style crew with hierarchy and delegation."""
    
    def __init__(
        self,
        agents: List[OpenClawAgent],
        manager: Optional[OpenClawAgent] = None,
        process: str = "sequential",
    ):
        self.agents = {a.name: a for a in agents}
        self.manager = manager
        self.process = process
    
    def add_agent(self, agent: OpenClawAgent):
        """Add agent to crew."""
        self.agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[OpenClawAgent]:
        """Get agent by name."""
        return self.agents.get(name)
    
    async def kickoff(self, task: str) -> Dict[str, Any]:
        """Execute crew on task."""
        if self.process == "hierarchical" and self.manager:
            plan = await self.manager._plan(task)
            assignments = await self._assign_tasks(plan)
            results = await self._execute_assignments(assignments)
            return results
        elif self.process == "parallel":
            return await self._parallel_execute(task)
        else:
            return await self._sequential_execute(task)
    
    async def _sequential_execute(self, task: str) -> Dict[str, str]:
        """Sequential execution."""
        results = {}
        remaining = task
        
        for agent in self.agents.values():
            result = await agent.execute(remaining)
            results[agent.name] = result
            remaining = result
        
        return results
    
    async def _parallel_execute(self, task: str) -> Dict[str, str]:
        """Parallel execution."""
        async def run_agent(agent):
            return agent.name, await agent.execute(task)
        
        results_list = await asyncio.gather(*[run_agent(a) for a in self.agents.values()])
        return dict(results_list)
    
    async def _assign_tasks(self, plan: List[str]) -> Dict[str, List[str]]:
        """Assign tasks to agents."""
        if not self.llm:
            return {name: [plan[i]] for i, name in enumerate(self.agents.keys())}
        
        assignment_prompt = f"""Assign these steps to agents:
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(plan))}

Agents: {', '.join(self.agents.keys())}"""
        
        # Simple round-robin for now
        assignments = {name: [] for name in self.agents.keys()}
        for i, step in enumerate(plan):
            agent_name = list(assignments.keys())[i % len(assignments)]
            assignments[agent_name].append(step)
        
        return assignments
    
    async def _execute_assignments(self, assignments: Dict[str, List[str]]) -> Dict[str, str]:
        """Execute assigned tasks."""
        results = {}
        for agent_name, tasks in assignments.items():
            agent = self.agents.get(agent_name)
            if agent:
                combined = " / ".join(tasks)
                results[agent_name] = await agent.execute(combined)
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_openshell_sandbox(sandbox_type: str = "docker") -> OpenShellBackend:
    """Create OpenShell sandbox backend."""
    config = SandboxConfig(sandbox_type=SandboxType(sandbox_type))
    return OpenShellBackend(config)


def create_openclaw_agent(
    name: str,
    responsibilities: List[str],
    llm: Any = None,
    team: Optional[str] = None,
) -> OpenClawAgent:
    """Create OpenClaw agent with soul config."""
    soul = SoulConfig(
        name=name,
        responsibilities=responsibilities,
        team=team,
        work_style=["autonomous", "thorough"],
    )
    return OpenClawAgent(name=name, soul=soul, llm=llm)


def create_openclaw_crew(
    agent_configs: List[Dict[str, Any]],
    llm: Any = None,
    process: str = "sequential",
) -> OpenClawCrew:
    """Create OpenClaw crew from configs."""
    agents = [
        create_openclaw_agent(
            name=cfg["name"],
            responsibilities=cfg.get("responsibilities", []),
            llm=llm,
            team=cfg.get("team"),
        )
        for cfg in agent_configs
    ]
    
    manager_name = next((c.get("manager") for c in agent_configs if c.get("is_manager")), None)
    manager = next((a for a in agents if a.name == manager_name), None) if manager_name else None
    
    return OpenClawCrew(agents=agents, manager=manager, process=process)
