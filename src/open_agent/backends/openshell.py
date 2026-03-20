"""OpenShell backend integration for deep agents.

This module provides integration with NVIDIA OpenShell sandbox runtime,
enabling secure, isolated execution environments for AI agents.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import structlog

from open_agent.config.settings import get_config, OpenShellConfig

logger = structlog.get_logger(__name__)


class SandboxType(str, Enum):
    """Types of sandbox environments."""
    DOCKER = "docker"
    K3S = "k3s"
    AUTO = "auto"


class SandboxSession:
    """Represents an OpenShell sandbox session."""

    def __init__(
        self,
        session_id: str,
        backend: "OpenShellBackend",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.session_id = session_id
        self.backend = backend
        self.metadata = metadata or {}

    def exec(self, command: str) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        return self.backend._execute_command(self.session_id, command)

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write a file to the sandbox."""
        return self.backend._write_file(self.session_id, path, content)

    def read_file(self, path: str) -> str:
        """Read a file from the sandbox."""
        return self.backend._read_file(self.session_id, path)

    def terminate(self) -> None:
        """Terminate the sandbox session."""
        self.backend._terminate_session(self.session_id)


class OpenShellBackend:
    """OpenShell sandbox backend for deep agents.

    This backend provides:
    - Isolated execution environments (Docker/K3s containers)
    - Policy-enforced filesystem, process, and network access
    - Privacy router for data protection
    - Credential injection for agents

    Uses NVIDIA OpenShell for secure agent execution with YAML-based policies.
    """

    def __init__(
        self,
        sandbox_type: SandboxType = SandboxType.AUTO,
        policy_file: Optional[str] = None,
        credential_provider: str = "nvidia",
        root_dir: Optional[str] = None,
    ):
        self.config = get_config().openshell
        self.sandbox_type = sandbox_type
        self.policy_file = policy_file or self.config.policy_file
        self.credential_provider = credential_provider
        self.root_dir = root_dir
        self._sessions: Dict[str, SandboxSession] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the OpenShell backend."""
        if self._initialized:
            return

        logger.info("initializing_openshell_backend", sandbox_type=self.sandbox_type)

        # Check if OpenShell CLI is available
        try:
            import subprocess
            result = subprocess.run(
                ["openshell", "--version"],
                capture_output=True,
                text=True,
            )
            logger.info("openshell_version", version=result.stdout.strip())
        except FileNotFoundError:
            logger.warning("openshell_not_found", message="OpenShell CLI not installed")

        self._initialized = True

    def create_sandbox(self, agent_type: str = "nemotron") -> SandboxSession:
        """Create a new sandbox session.

        Args:
            agent_type: Type of agent to run (e.g., 'nemotron', 'claude', 'opencode')

        Returns:
            SandboxSession instance
        """
        if not self._initialized:
            self.initialize()

        import uuid
        session_id = f"sandbox_{uuid.uuid4().hex[:12]}"

        logger.info("creating_sandbox", session_id=session_id, agent_type=agent_type)

        # Try to use openshell CLI
        try:
            import subprocess
            cmd = [
                "openshell", "sandbox", "create",
                "--from", agent_type,
            ]
            if self.config.remote_host:
                cmd.extend(["--remote", self.config.remote_host])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                logger.info("sandbox_created", session_id=session_id, output=result.stdout)
            else:
                logger.warning("sandbox_creation_failed", error=result.stderr)

        except Exception as e:
            logger.error("sandbox_creation_error", error=str(e))

        session = SandboxSession(session_id=session_id, backend=self)
        self._sessions[session_id] = session
        return session

    def _execute_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Execute a command in a sandbox session."""
        logger.debug("executing_command", session_id=session_id, command=command)

        try:
            import subprocess
            result = subprocess.run(
                ["openshell", "exec", session_id, command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }

    def _write_file(self, session_id: str, path: str, content: str) -> Dict[str, Any]:
        """Write a file to the sandbox."""
        import base64
        content_b64 = base64.b64encode(content.encode()).decode()

        try:
            import subprocess
            result = subprocess.run(
                ["openshell", "file", "write", session_id, path, content_b64],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return {
                "success": result.returncode == 0,
                "path": path,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _read_file(self, session_id: str, path: str) -> str:
        """Read a file from the sandbox."""
        try:
            import subprocess
            result = subprocess.run(
                ["openshell", "file", "read", session_id, path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                import base64
                return base64.b64decode(result.stdout).decode()

        except Exception as e:
            logger.error("read_file_error", session_id=session_id, path=path, error=str(e))

        return ""

    def _terminate_session(self, session_id: str) -> None:
        """Terminate a sandbox session."""
        if session_id in self._sessions:
            try:
                import subprocess
                subprocess.run(
                    ["openshell", "sandbox", "stop", session_id],
                    capture_output=True,
                    timeout=10,
                )
            except Exception as e:
                logger.error("terminate_session_error", session_id=session_id, error=str(e))

            del self._sessions[session_id]
            logger.info("session_terminated", session_id=session_id)

    def list_sessions(self) -> List[str]:
        """List active sandbox sessions."""
        return list(self._sessions.keys())

    def get_session(self, session_id: str) -> Optional[SandboxSession]:
        """Get a sandbox session by ID."""
        return self._sessions.get(session_id)


def create_openshell_backend(
    sandbox_type: str = "auto",
    policy_file: Optional[str] = None,
) -> OpenShellBackend:
    """Create an OpenShell backend.

    Example:
        >>> from open_agent.backends.openshell import create_openshell_backend
        >>>
        >>> backend = create_openshell_backend(
        ...     sandbox_type="docker",
        ...     policy_file="./policy.yaml"
        ... )
        >>> session = backend.create_sandbox("nemotron")
    """
    return OpenShellBackend(
        sandbox_type=SandboxType(sandbox_type),
        policy_file=policy_file,
    )


# Global backend instance
_global_backend: Optional[OpenShellBackend] = None


def get_default_backend() -> OpenShellBackend:
    """Get or create the default OpenShell backend."""
    global _global_backend
    if _global_backend is None:
        _global_backend = create_openshell_backend()
    return _global_backend
