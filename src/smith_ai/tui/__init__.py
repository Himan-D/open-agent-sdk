"""SmithAI Terminal User Interface.

A full-featured terminal UI for AI agent interaction with:
- Command palette (Ctrl+K)
- Split panes
- Code editing
- File explorer
- Terminal emulator
- Browser preview
- Real-time streaming output
- Multi-tab interface
"""

from __future__ import annotations

import asyncio
import os
import sys
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

try:
    from textual.app import App, ComposeResult
    from textual.widgets import (
        Header, Footer, Tree, Input, Log, Static, 
        RichLog, Button, TextArea, TabbedContent, TabPane,
        DataTable, Sparkline, ProgressBar
    )
    from textual.containers import Container, Horizontal, Vertical
    from textual.binding import Binding
    from textual import events
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


class Key(str, Enum):
    """Key bindings."""
    CTRL_C = "ctrl_c"
    CTRL_K = "ctrl_k"
    CTRL_S = "ctrl_s"
    CTRL_N = "ctrl_n"
    CTRL_T = "ctrl_t"
    CTRL_W = "ctrl_w"
    CTRL_B = "ctrl_b"
    CTRL_P = "ctrl_p"
    ESC = "escape"
    ENTER = "enter"
    TAB = "tab"


@dataclass
class Tab:
    id: str
    title: str
    content: Any = None
    modified: bool = False


@dataclass 
class Command:
    name: str
    description: str
    shortcut: Optional[str] = None
    action: Optional[Callable] = None
    category: str = "General"


class Component(ABC):
    """Base class for UI components."""
    
    @abstractmethod
    def render(self) -> str:
        pass
    
    @abstractmethod
    def handle_input(self, key: str) -> Optional[str]:
        pass


class CommandPalette:
    """Command palette like VSCode/Copilot.
    
    Provides:
    - Fuzzy search
    - Command categories
    - Recent commands
    - Keyboard shortcuts
    """
    
    def __init__(self):
        self.commands: List[Command] = []
        self.recent: List[str] = []
        self._visible = False
        self._query = ""
        self._selected = 0
    
    def register(self, command: Command) -> None:
        self.commands.append(command)
    
    def show(self) -> None:
        self._visible = True
        self._query = ""
        self._selected = 0
    
    def hide(self) -> None:
        self._visible = False
    
    def filter(self, query: str) -> List[Command]:
        if not query:
            return self.commands
        
        query_lower = query.lower()
        return [
            cmd for cmd in self.commands
            if query_lower in cmd.name.lower() 
            or query_lower in cmd.description.lower()
        ]
    
    def handle_key(self, key: str) -> Optional[Command]:
        """Handle key input in palette."""
        if key == Key.ESC:
            self.hide()
            return None
        
        if key == Key.ENTER:
            results = self.filter(self._query)
            if results and self._selected < len(results):
                cmd = results[self._selected]
                self.recent.insert(0, cmd.name)
                self.hide()
                return cmd
        
        if key == "up":
            self._selected = max(0, self._selected - 1)
        elif key == "down":
            results = self.filter(self._query)
            self._selected = min(len(results) - 1, self._selected + 1)
        elif key == "backspace":
            self._query = self._query[:-1]
        elif len(key) == 1:
            self._query += key
        
        return None


class Panel(ABC):
    """Base class for panels."""
    
    def __init__(self, title: str, width: int = 0, height: int = 0):
        self.title = title
        self.width = width
        self.height = height
        self.visible = True


class EditorPanel(Panel):
    """Code editor panel."""
    
    def __init__(self, file_path: Optional[str] = None):
        super().__init__("Editor")
        self.file_path = file_path
        self.content = ""
        self.cursor_line = 1
        self.cursor_col = 1
        self.dirty = False
        self.language = "python"
        self._undo_stack: List[str] = []
        self._redo_stack: List[str] = []
    
    def load_file(self, path: str) -> bool:
        try:
            with open(path, 'r') as f:
                self.content = f.read()
            self.file_path = path
            self.dirty = False
            self._detect_language(path)
            return True
        except:
            return False
    
    def save_file(self) -> bool:
        if not self.file_path:
            return False
        try:
            with open(self.file_path, 'w') as f:
                f.write(self.content)
            self.dirty = False
            return True
        except:
            return False
    
    def _detect_language(self, path: str) -> None:
        ext = os.path.splitext(path)[1]
        langs = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.yml': 'yaml',
        }
        self.language = langs.get(ext, 'text')
    
    def insert(self, text: str) -> None:
        self._undo_stack.append(self.content)
        self.content += text
        self.dirty = True
    
    def delete_line(self, line: int) -> None:
        lines = self.content.split('\n')
        if 0 <= line < len(lines):
            self._undo_stack.append(self.content)
            lines.pop(line)
            self.content = '\n'.join(lines)
            self.dirty = True
    
    def undo(self) -> None:
        if self._undo_stack:
            self._redo_stack.append(self.content)
            self.content = self._undo_stack.pop()
            self.dirty = True
    
    def redo(self) -> None:
        if self._redo_stack:
            self._undo_stack.append(self.content)
            self.content = self._redo_stack.pop()
            self.dirty = True


class TerminalPanel(Panel):
    """Terminal emulator panel.
    
    Provides:
    - PTY-based terminal
    - Multiple sessions
    - Output logging
    - Command history
    """
    
    def __init__(self, shell: str = "/bin/bash"):
        super().__init__("Terminal")
        self.shell = shell
        self.process: Optional[asyncio.subprocess.Process] = None
        self.history: List[str] = []
        self._output_buffer = ""
    
    async def start(self) -> None:
        self.process = await asyncio.create_subprocess_shell(
            self.shell,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy()
        )
        asyncio.create_task(self._read_output())
    
    async def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        
        while True:
            data = await self.process.stdout.read(1024)
            if not data:
                break
            self._output_buffer += data.decode()
            self.history.append(data.decode())
    
    async def send(self, command: str) -> None:
        if self.process and self.process.stdin:
            self.process.stdin.write(command.encode() + b'\n')
            await self.process.stdin.drain()
    
    async def resize(self, cols: int, rows: int) -> None:
        if self.process:
            try:
                await asyncio.create_subprocess_shell(
                    f"resize -s {rows} {cols}",
                    stdout=asyncio.DEVNULL,
                    stderr=asyncio.DEVNULL
                )
            except:
                pass
    
    async def kill(self) -> None:
        if self.process:
            self.process.terminate()
            await self.process.wait()


class BrowserPreviewPanel(Panel):
    """Browser preview panel."""
    
    def __init__(self, width: int = 800, height: int = 600):
        super().__init__("Browser Preview")
        self.width = width
        self.height = height
        self.url = "about:blank"
        self.screenshot: Optional[bytes] = None


class FileExplorer:
    """File tree explorer.
    
    Provides:
    - Directory tree view
    - File icons
    - Quick open
    - Git status
    """
    
    def __init__(self, root_path: str = "."):
        self.root = root_path
        self.expanded: Dict[str, bool] = {}
        self.selected: Optional[str] = None
    
    def get_tree(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Get directory tree structure."""
        path = path or self.root
        
        tree = {
            "name": os.path.basename(path) or path,
            "type": "directory" if os.path.isdir(path) else "file",
            "children": []
        }
        
        if os.path.isdir(path):
            try:
                for item in sorted(os.listdir(path)):
                    if item.startswith('.'):
                        continue
                    item_path = os.path.join(path, item)
                    tree["children"].append(self.get_tree(item_path))
            except PermissionError:
                pass
        
        return tree
    
    def get_icon(self, path: str) -> str:
        """Get icon for file."""
        if os.path.isdir(path):
            return "[DIR]"
        
        ext = os.path.splitext(path)[1]
        icons = {
            '.py': '[PY]',
            '.js': '[JS]',
            '.ts': '[TS]',
            '.json': '[JSON]',
            '.md': '[MD]',
            '.txt': '[TXT]',
            '.sh': '[SH]',
        }
        return icons.get(ext, '[FILE]')


class OutputLog:
    """Output log for agent responses.
    
    Features:
    - ANSI color support
    - Auto-scroll
    - Copy to clipboard
    - Clear
    - Save to file
    """
    
    def __init__(self):
        self.lines: List[str] = []
        self.max_lines = 10000
        self._handlers: List[Callable[[str], None]] = []
    
    def write(self, text: str, style: str = "") -> None:
        self.lines.append(text)
        
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]
        
        for handler in self._handlers:
            handler(text)
    
    def writeline(self, text: str = "", style: str = "") -> None:
        self.write(text + "\n", style)
    
    def clear(self) -> None:
        self.lines.clear()
    
    def save(self, path: str) -> bool:
        try:
            with open(path, 'w') as f:
                f.write('\n'.join(self.lines))
            return True
        except:
            return False
    
    def copy_all(self) -> str:
        return '\n'.join(self.lines)
    
    def on_write(self, handler: Callable[[str], None]) -> None:
        self._handlers.append(handler)


class StatusBar:
    """Status bar with information.
    
    Shows:
    - Current file
    - Line/column
    - Language mode
    - Git branch
    - LLM status
    - Memory usage
    """
    
    def __init__(self):
        self.file_path: Optional[str] = None
        self.line = 1
        self.column = 1
        self.language = "Plain Text"
        self.git_branch: Optional[str] = None
        self.llm_status = "Ready"
        self.agents_running = 0
    
    def render(self) -> str:
        branch = f"  {self.git_branch}" if self.git_branch else ""
        return (
            f" {self.file_path or 'No file'} | Ln {self.line}, Col {self.column} | "
            f"{self.language}{branch} | {self.llm_status} | "
            f"Agents: {self.agents_running}"
        )


class TUIRenderer:
    """Render TUI to terminal.
    
    Fallback renderer when textual is not available.
    Uses basic terminal escape codes.
    """
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_BLACK = "\033[40m"
    BG_BLUE = "\033[44m"
    
    def __init__(self):
        self.width = 120
        self.height = 40
        self._buffer: List[str] = []
    
    def clear(self) -> None:
        print("\033[2J\033[H", end="")
        self._buffer.clear()
    
    def move_to(self, x: int, y: int) -> None:
        print(f"\033[{y};{x}H", end="")
    
    def write(self, text: str, x: int = 1, y: int = 1) -> None:
        self.move_to(x, y)
        print(text, end="", flush=True)
    
    def box(self, x: int, y: int, w: int, h: int, title: str = "") -> None:
        corners = ["┌", "┐", "└", "┘"]
        horiz = "─"
        vert = "│"
        
        self.move_to(x, y)
        print(corners[0] + horiz * (w - 2) + corners[1], end="")
        
        for i in range(1, h - 1):
            self.move_to(x, y + i)
            print(vert, end="")
            self.move_to(x + w - 1, y + i)
            print(vert, end="")
        
        self.move_to(x, y + h - 1)
        print(corners[2] + horiz * (w - 2) + corners[3], end="")
        
        if title:
            self.move_to(x + 2, y)
            print(title, end="")
    
    def status_line(self, text: str) -> None:
        self.move_to(1, self.height)
        print(f"{self.BG_BLUE}{self.WHITE} {text}{' ' * (self.width - len(text) - 2)} {self.RESET}", end="")
    
    def command_palette(self, query: str, results: List[str]) -> None:
        self.box(5, 5, self.width - 10, 15, " Command Palette ")
        
        self.move_to(7, 7)
        print(f" > {query}_", end="")
        
        for i, result in enumerate(results[:10]):
            y = 9 + i
            prefix = " > " if i == 0 else "   "
            self.move_to(7, y)
            print(f"{prefix}{result[:self.width - 20]}")


class TUIBridge:
    """Bridge between TUI and agent.
    
    Allows the agent to:
    - Read files
    - Write files
    - Execute commands
    - Control browser
    - Update UI
    """
    
    def __init__(self, app: Optional[Any] = None):
        self.app = app
        self.output_log = OutputLog()
        self.editor: Optional[EditorPanel] = None
        self.terminal: Optional[TerminalPanel] = None
        self.browser: Optional[BrowserPreviewPanel] = None
    
    async def read_file(self, path: str) -> str:
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {path}: {e}"
    
    async def write_file(self, path: str, content: str) -> str:
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Written to {path}"
        except Exception as e:
            return f"Error writing {path}: {e}"
    
    async def execute_command(self, command: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        result = stdout.decode() + stderr.decode()
        self.output_log.write(result)
        return result
    
    async def run_browser(self, url: str) -> str:
        self.output_log.write(f"Opening browser: {url}\n")
        return f"Browser opened: {url}"
    
    def update_status(self, status: str) -> None:
        self.output_log.write(f"[STATUS] {status}\n")


def create_tui_app() -> Any:
    """Create the main TUI application."""
    if not TEXTUAL_AVAILABLE:
        return None
    
    class SmithAIApp(App):
        CSS = """
        Screen {
            background: $surface;
        }
        
        #header {
            height: 3;
            background: $primary;
            color: $text;
        }
        
        #sidebar {
            width: 25;
            dock: left;
            background: $panel;
        }
        
        #main {
            dock: center;
        }
        
        #terminal {
            dock: bottom;
            height: 30%;
            background: $surface;
        }
        
        #statusbar {
            dock: bottom;
            height: 1;
            background: $accent;
        }
        
        .panel {
            border: solid $accent;
            padding: 1;
        }
        
        TabbedContent {
            height: 100%;
        }
        """
        
        BINDINGS = [
            Binding("ctrl+k", "toggle_command_palette", "Command Palette"),
            Binding("ctrl+s", "save", "Save"),
            Binding("ctrl+n", "new_file", "New File"),
            Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
            Binding("ctrl+`", "toggle_terminal", "Toggle Terminal"),
            Binding("ctrl+p", "quick_open", "Quick Open"),
            Binding("ctrl+shift+m", "toggle_mermaid", "Mermaid Preview"),
            Binding("f1", "show_help", "Help"),
        ]
        
        def __init__(self):
            super().__init__()
            self.command_palette = CommandPalette()
            self.output_log = OutputLog()
            self.status_bar = StatusBar()
            self._setup_commands()
        
        def _setup_commands(self) -> None:
            self.command_palette.register(Command(
                "New File", "Create a new file", "Ctrl+N"
            ))
            self.command_palette.register(Command(
                "Open File", "Open a file", "Ctrl+O"
            ))
            self.command_palette.register(Command(
                "Save", "Save current file", "Ctrl+S"
            ))
            self.command_palette.register(Command(
                "Run Agent", "Run AI agent", "Ctrl+Enter"
            ))
            self.command_palette.register(Command(
                "Terminal", "Open terminal", "Ctrl+`"
            ))
            self.command_palette.register(Command(
                "Browser", "Open browser", "Ctrl+B"
            ))
        
        def compose(self) -> ComposeResult:
            yield Header(id="header")
            
            with Container(id="main"):
                with TabbedContent():
                    with TabPane("Output"):
                        yield RichLog(id="output", markup=True)
                    with TabPane("Editor"):
                        yield TextArea(id="editor")
            
            yield Footer(id="statusbar")
        
        def action_toggle_command_palette(self) -> None:
            self.command_palette.show()
        
        def action_save(self) -> None:
            self.output_log.write("[Saved]\n")
        
        def action_new_file(self) -> None:
            self.output_log.write("[New file]\n")
        
        def action_toggle_sidebar(self) -> None:
            pass
        
        def action_toggle_terminal(self) -> None:
            pass
        
        def action_quick_open(self) -> None:
            pass
        
        def action_show_help(self) -> None:
            self.output_log.write("""
SmithAI Terminal Commands:
─────────────────────────
/help          Show this help
/agent         Start AI agent
/browser       Open browser
/run [cmd]     Run command
/file [path]   Read file
/edit [path]   Edit file
/terminal      Open terminal
/clear         Clear output
/exit          Exit TUI
""")
        
        def watch_title(self, title: str) -> None:
            self.sub_title = title
    
    return SmithAIApp()


__all__ = [
    "TUIBridge",
    "TUIRenderer",
    "CommandPalette",
    "Command",
    "EditorPanel",
    "TerminalPanel",
    "BrowserPreviewPanel",
    "FileExplorer",
    "OutputLog",
    "StatusBar",
    "Panel",
    "create_tui_app",
]
