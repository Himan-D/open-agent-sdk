"""Filesystem tools for file operations."""

from typing import Optional
from open_agent.agents.tools.base import BaseTool, PermissionLevel
from open_agent.agents.sandbox.backend import OpenShellBackend, SandboxSession
import structlog

logger = structlog.get_logger(__name__)


class FileTools(BaseTool):
    """File system tools (ls, read, write, edit).
    
    Provides safe filesystem operations within a sandboxed environment,
    similar to OpenClaw's filesystem tools.
    
    Example:
        >>> backend = OpenShellBackend()
        >>> tools = FileTools(backend=backend)
        >>> content = await tools.read_file("/path/to/file")
        >>> await tools.write_file("/path/to/file", "content")
    """

    def __init__(self, backend: Optional[OpenShellBackend] = None):
        super().__init__(
            name="filesystem",
            description="File system operations",
            permission_level=PermissionLevel.WRITE,
        )
        self.backend = backend
        self.session: Optional[SandboxSession] = None

    def _get_session(self) -> SandboxSession:
        """Get or create a sandbox session."""
        if self.session is None:
            if self.backend is None:
                self.backend = OpenShellBackend()
            self.session = self.backend.create_sandbox("nemotron")
        return self.session

    async def ls(self, path: str = ".") -> str:
        """List directory contents.
        
        Args:
            path: Directory path to list
            
        Returns:
            Directory listing
        """
        session = self._get_session()
        result = session.exec(f"ls -la {path}")
        return result.get("stdout", "")

    async def read_file(self, path: str) -> str:
        """Read a file.
        
        Args:
            path: File path to read
            
        Returns:
            File contents or error
        """
        session = self._get_session()
        return session.read_file(path)

    async def write_file(self, path: str, content: str) -> str:
        """Write a file.
        
        Args:
            path: File path to write
            content: Content to write
            
        Returns:
            Success or error message
        """
        session = self._get_session()
        result = session.write_file(path, content)
        if result.get("success"):
            return f"File written successfully: {path}"
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    async def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """Edit a file (replace old_text with new_text).
        
        Args:
            path: File path to edit
            old_text: Text to replace
            new_text: Replacement text
            
        Returns:
            Success or error message
        """
        content = await self.read_file(path)
        content = content.replace(old_text, new_text)
        return await self.write_file(path, content)
