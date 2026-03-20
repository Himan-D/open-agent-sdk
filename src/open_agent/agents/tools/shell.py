"""Shell tool for executing commands in sandbox."""

from typing import Optional
from open_agent.agents.tools.base import BaseTool, PermissionLevel
from open_agent.agents.sandbox.backend import OpenShellBackend, SandboxSession
import structlog

logger = structlog.get_logger(__name__)


class ShellTool(BaseTool):
    """Tool for shell command execution via OpenShell sandbox.
    
    Provides secure shell command execution within a sandboxed environment,
    similar to OpenClaw's exec tool.
    
    Example:
        >>> backend = OpenShellBackend()
        >>> tool = ShellTool(backend=backend)
        >>> result = await tool.execute(command="ls -la")
    """

    def __init__(self, backend: Optional[OpenShellBackend] = None):
        super().__init__(
            name="execute",
            description="Execute a shell command in the sandbox",
            permission_level=PermissionLevel.EXEC,
        )
        self.backend = backend
        self.session: Optional[SandboxSession] = None

    async def execute(self, command: str, **kwargs) -> str:
        """Execute a shell command.
        
        Args:
            command: The shell command to execute
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Command output or error message
        """
        if self.session is None:
            if self.backend is None:
                self.backend = OpenShellBackend()
            self.session = self.backend.create_sandbox("nemotron")

        result = self.session.exec(command)
        if result.get("success"):
            return result.get("stdout", "")
        else:
            return f"Error: {result.get('stderr', 'Unknown error')}"
