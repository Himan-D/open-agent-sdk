"""Sandbox execution environment for safe code execution."""

from __future__ import annotations

import asyncio
import subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from smith_ai.core.types import BaseTool, ToolResult


@dataclass
class SandboxConfig:
    timeout: int = 30
    memory_limit: str = "256m"
    cpu_limit: str = "0.5"
    network_enabled: bool = False
    read_only_fs: bool = True


class SandboxSession:
    """A sandboxed execution session."""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._session_id = None
        self._running = False
    
    def exec(self, command: str) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {self.config.timeout}s",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }
    
    async def exec_async(self, command: str) -> Dict[str, Any]:
        """Execute a command asynchronously."""
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.config.timeout)
                return {
                    "success": proc.returncode == 0,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "returncode": proc.returncode,
                }
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Command timed out after {self.config.timeout}s",
                    "returncode": -1,
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }
    
    def terminate(self) -> None:
        """Terminate the session."""
        self._running = False


class Sandbox:
    """Sandbox manager for isolated code execution."""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._sessions: List[SandboxSession] = []
    
    def create_session(self) -> SandboxSession:
        """Create a new sandbox session."""
        session = SandboxSession(self.config)
        self._sessions.append(session)
        return session
    
    def exec(self, command: str) -> Dict[str, Any]:
        """Execute in a new session."""
        session = self.create_session()
        result = session.exec(command)
        session.terminate()
        return result
    
    async def exec_async(self, command: str) -> Dict[str, Any]:
        """Execute asynchronously in a new session."""
        session = self.create_session()
        result = await session.exec_async(command)
        session.terminate()
        return result
    
    def exec_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely."""
        return self.exec(f'python3 -c "{code.replace(chr(34), chr(92)+chr(34))}"')
    
    async def exec_python_async(self, code: str) -> Dict[str, Any]:
        """Execute Python code asynchronously."""
        return await self.exec_async(f'python3 -c "{code.replace(chr(34), chr(92)+chr(34))}"')


class SandboxTool(BaseTool):
    """Tool for sandboxed code execution."""
    
    name = "sandbox_exec"
    description = "Execute code in a sandboxed environment"
    category = "automation"
    
    def __init__(self):
        self._sandbox = Sandbox()
    
    async def execute(self, command: str, language: str = "shell") -> ToolResult:
        """Execute code in sandbox."""
        try:
            if language == "python":
                result = await self._sandbox.exec_python_async(command)
            else:
                result = await self._sandbox.exec_async(command)
            
            output = result.get("stdout", "")
            if not result.get("success"):
                output = f"Error: {result.get('stderr', 'Unknown error')}"
            
            return ToolResult(tool_call_id="", success=result.get("success", False), output=output)
        
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


from smith_ai.core.types import BaseTool, ToolResult

__all__ = [
    "Sandbox",
    "SandboxSession",
    "SandboxConfig",
    "SandboxTool",
]
