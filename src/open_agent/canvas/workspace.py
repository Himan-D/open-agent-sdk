"""Canvas workspace - Interactive code editing environment."""

from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import structlog

logger = structlog.get_logger(__name__)


class FileType(str, Enum):
    """Supported file types."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    TEXT = "text"


@dataclass
class Cursor:
    """Cursor position in a file."""
    line: int = 0
    column: int = 0


@dataclass
class Selection:
    """Text selection in a file."""
    start: Cursor
    end: Cursor
    text: str = ""


@dataclass
class CanvasFile:
    """A file in the canvas workspace."""
    path: str
    content: str
    language: FileType = FileType.TEXT
    modified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    cursor: Cursor = field(default_factory=Cursor)
    selection: Optional[Selection] = None

    def get_language_from_extension(self) -> FileType:
        """Detect language from file extension."""
        ext_map = {
            ".py": FileType.PYTHON,
            ".js": FileType.JAVASCRIPT,
            ".ts": FileType.TYPESCRIPT,
            ".html": FileType.HTML,
            ".css": FileType.CSS,
            ".json": FileType.JSON,
            ".md": FileType.MARKDOWN,
            ".yaml": FileType.YAML,
            ".yml": FileType.YAML,
        }
        
        for ext, lang in ext_map.items():
            if self.path.endswith(ext):
                return lang
        return FileType.TEXT


@dataclass
class CanvasSession:
    """A canvas editing session."""
    session_id: str
    files: Dict[str, CanvasFile] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_file(self, path: str, content: str = "") -> CanvasFile:
        """Add a file to the session."""
        file = CanvasFile(path=path, content=content)
        file.language = file.get_language_from_extension()
        self.files[path] = file
        self.last_activity = datetime.now()
        return file

    def get_file(self, path: str) -> Optional[CanvasFile]:
        """Get a file by path."""
        return self.files.get(path)

    def remove_file(self, path: str) -> bool:
        """Remove a file from the session."""
        if path in self.files:
            del self.files[path]
            self.last_activity = datetime.now()
            return True
        return False

    def list_files(self) -> List[str]:
        """List all files in the session."""
        return list(self.files.keys())


class Canvas:
    """Interactive canvas workspace for code editing.
    
    Similar to OpenClaw's Canvas for providing an interactive
    coding environment for agents.
    
    Example:
        >>> canvas = Canvas()
        >>> session = canvas.create_session("my-workspace")
        >>> canvas.write_file(session.session_id, "main.py", "print('Hello')")
        >>> content = canvas.read_file(session.session_id, "main.py")
        >>> print(content)
    """

    def __init__(self, root_path: Optional[str] = None):
        self.root_path = root_path or "/tmp/canvas"
        self.sessions: Dict[str, CanvasSession] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "file_created": [],
            "file_modified": [],
            "file_deleted": [],
            "session_created": [],
            "session_closed": [],
        }

    def create_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CanvasSession:
        """Create a new canvas session."""
        session = CanvasSession(
            session_id=session_id,
            metadata=metadata or {},
        )
        self.sessions[session_id] = session
        self._trigger_hook("session_created", session)
        logger.info("canvas_session_created", session_id=session_id)
        return session

    def get_session(self, session_id: str) -> Optional[CanvasSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        """Close a canvas session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            self._trigger_hook("session_closed", session)
            logger.info("canvas_session_closed", session_id=session_id)
            return True
        return False

    def write_file(
        self,
        session_id: str,
        path: str,
        content: str,
    ) -> bool:
        """Write content to a file."""
        session = self.get_session(session_id)
        if not session:
            return False

        existing = session.get_file(path)
        if existing:
            existing.content = content
            existing.modified = True
            existing.modified_at = datetime.now()
        else:
            session.add_file(path, content)

        self._trigger_hook("file_modified", session, path, content)
        logger.debug("canvas_file_written", session_id=session_id, path=path)
        return True

    def read_file(self, session_id: str, path: str) -> Optional[str]:
        """Read content from a file."""
        session = self.get_session(session_id)
        if not session:
            return None

        file = session.get_file(path)
        if file:
            return file.content
        return None

    def delete_file(self, session_id: str, path: str) -> bool:
        """Delete a file from the session."""
        session = self.get_session(session_id)
        if not session:
            return False

        if session.remove_file(path):
            self._trigger_hook("file_deleted", session, path)
            return True
        return False

    def execute_file(
        self,
        session_id: str,
        path: str,
        interpreter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a file and return results.
        
        Args:
            session_id: Canvas session ID
            path: Path to the file to execute
            interpreter: Override interpreter (e.g., "python3", "node")
            
        Returns:
            Dict with stdout, stderr, returncode
        """
        import subprocess
        import tempfile
        import os

        content = self.read_file(session_id, path)
        if content is None:
            return {"success": False, "error": "File not found", "stdout": "", "stderr": ""}

        session = self.get_session(session_id)
        file = session.get_file(path)
        
        if file.language == FileType.PYTHON:
            cmd = [interpreter or "python3"]
        elif file.language == FileType.JAVASCRIPT:
            cmd = [interpreter or "node"]
        elif file.language == FileType.TYPESCRIPT:
            cmd = ["npx", "ts-node"]
        else:
            return {
                "success": False,
                "error": f"No interpreter for {file.language}",
                "stdout": "",
                "stderr": "",
            }

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=path,
            delete=False
        ) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = subprocess.run(
                cmd + [temp_path],
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
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timed out",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"{cmd[0]} not found",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
            }
        finally:
            os.unlink(temp_path)

    def apply_edit(
        self,
        session_id: str,
        path: str,
        old_text: str,
        new_text: str,
    ) -> bool:
        """Apply a text edit to a file.
        
        Args:
            session_id: Canvas session ID
            path: File path
            old_text: Text to replace
            new_text: Replacement text
            
        Returns:
            True if edit was applied
        """
        content = self.read_file(session_id, path)
        if content is None:
            return False

        if old_text not in content:
            return False

        new_content = content.replace(old_text, new_text)
        return self.write_file(session_id, path, new_content)

    def insert_text(
        self,
        session_id: str,
        path: str,
        text: str,
        line: Optional[int] = None,
        column: int = 0,
    ) -> bool:
        """Insert text at a specific position.
        
        Args:
            session_id: Canvas session ID
            path: File path
            text: Text to insert
            line: Line number (0-indexed), appends if None
            column: Column position
            
        Returns:
            True if text was inserted
        """
        content = self.read_file(session_id, path)
        if content is None:
            return False

        lines = content.split('\n')
        
        if line is None:
            lines.append(text)
        elif line < len(lines):
            line_content = lines[line]
            lines[line] = line_content[:column] + text + line_content[column:]
        else:
            while len(lines) < line:
                lines.append('')
            lines.append(text)

        new_content = '\n'.join(lines)
        return self.write_file(session_id, path, new_content)

    def get_file_tree(self, session_id: str) -> Dict[str, Any]:
        """Get a tree structure of all files in the session."""
        session = self.get_session(session_id)
        if not session:
            return {}

        tree = {"type": "folder", "name": "/", "children": {}}
        
        for path in sorted(session.files.keys()):
            parts = path.strip("/").split("/")
            current = tree["children"]
            
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    file = session.get_file(path)
                    current[part] = {
                        "type": "file",
                        "name": part,
                        "path": path,
                        "language": file.language.value if file else "text",
                        "modified": file.modified if file else False,
                    }
                else:
                    if part not in current:
                        current[part] = {"type": "folder", "name": part, "children": {}}
                    current = current[part]["children"]

        return tree

    def register_hook(self, event: str, handler: Callable) -> None:
        """Register a hook handler."""
        if event in self._hooks:
            self._hooks[event].append(handler)

    def _trigger_hook(self, event: str, *args, **kwargs) -> None:
        """Trigger all handlers for an event."""
        for handler in self._hooks.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error("canvas_hook_error", event=event, error=str(e))

    def list_sessions(self) -> List[str]:
        """List all active sessions."""
        return list(self.sessions.keys())


def create_canvas(root_path: Optional[str] = None) -> Canvas:
    """Create a new canvas workspace.
    
    Example:
        >>> canvas = create_canvas("/tmp/my-workspace")
    """
    return Canvas(root_path=root_path)
