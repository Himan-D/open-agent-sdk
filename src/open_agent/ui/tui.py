"""TUI - Terminal User Interface for OpenAgent.

Provides an interactive terminal UI similar to OpenClaw's TUI.
"""

import asyncio
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import sys
import structlog

logger = structlog.get_logger(__name__)


class PanelType(str, Enum):
    """TUI panel types."""
    SESSIONS = "sessions"
    CHAT = "chat"
    SKILLS = "skills"
    MEMORY = "memory"
    STATUS = "status"


@dataclass
class TUIColor:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


class TUIPanel:
    """A panel in the TUI."""

    def __init__(self, title: str, width: int = 40, height: int = 20):
        self.title = title
        self.width = width
        self.height = height
        self.content: list = []

    def add_line(self, line: str, color: str = "") -> None:
        """Add a line to the panel."""
        self.content.append(f"{color}{line}{TUIColor.RESET}")

    def clear(self) -> None:
        """Clear panel content."""
        self.content = []

    def render(self) -> str:
        """Render the panel as a string."""
        lines = []
        border = "─" * self.width

        lines.append(f"┌─ {self.title} {border[len(self.title) + 3:]}┐")
        for line in self.content[-self.height:]:
            padded = line[:self.width]
            lines.append(f"│ {padded}{' ' * (self.width - len(padded))} │")
        lines.append(f"└{'─' * (self.width + 2)}┘")

        return "\n".join(lines)


class TUI:
    """Terminal User Interface."""

    def __init__(
        self,
        agent: Any = None,
        gateway: Any = None,
        on_message: Optional[Callable] = None,
    ):
        self.agent = agent
        self.gateway = gateway
        self.on_message = on_message

        self.current_panel = PanelType.CHAT
        self.panels: dict[PanelType, TUIPanel] = {}
        self.chat_history: list = []
        self.input_buffer = ""
        self.cursor_pos = 0
        self.running = False

        self._setup_panels()

    def _setup_panels(self) -> None:
        """Setup TUI panels."""
        self.panels[PanelType.CHAT] = TUIPanel("Chat", width=60, height=25)
        self.panels[PanelType.SESSIONS] = TUIPanel("Sessions", width=30, height=15)
        self.panels[PanelType.SKILLS] = TUIPanel("Skills", width=30, height=15)
        self.panels[PanelType.MEMORY] = TUIPanel("Memory", width=30, height=15)
        self.panels[PanelType.STATUS] = TUIPanel("Status", width=30, height=10)

    def _render_header(self) -> str:
        """Render the header."""
        return f"""{TUIColor.CYAN}{TUIColor.BOLD}
╔══════════════════════════════════════════════════════════════╗
║  OpenAgent TUI {TUIColor.DIM}v1.0.0{TUIColor.CYAN}                                           ║
║  Powered by NVIDIA Nemotron + OpenShell                      ║
╚══════════════════════════════════════════════════════════════╝
{TUIColor.RESET}"""

    def _render_panels(self) -> str:
        """Render all visible panels."""
        output = []

        # Header
        output.append(self._render_header())

        # Chat panel (main)
        chat = self.panels[PanelType.CHAT]
        chat_output = chat.render()
        output.append(chat_output)

        # Side panel
        side = self.panels[PanelType.STATUS]
        side_output = side.render()
        output.append(side_output)

        return "\n".join(output)

    def _update_status_panel(self) -> None:
        """Update the status panel."""
        panel = self.panels[PanelType.STATUS]
        panel.clear()

        panel.add_line(f"Agent: {self.agent.name if self.agent else 'None'}", TUIColor.GREEN)
        panel.add_line(f"Model: nemotron", TUIColor.DIM)
        panel.add_line("")
        panel.add_line("Panels:", TUIColor.BOLD)
        for p in PanelType:
            marker = ">" if p == self.current_panel else " "
            panel.add_line(f"  [{marker}] {p.value}")

    def _update_chat_panel(self) -> None:
        """Update the chat panel."""
        panel = self.panels[PanelType.CHAT]
        panel.clear()

        for msg in self.chat_history[-25:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            color = TUIColor.BLUE if role == "user" else TUIColor.GREEN
            panel.add_line(f"[{role}]", color)
            for line in content.split("\n")[:3]:
                panel.add_line(f"  {line[:70]}", TUIColor.DIM)
            panel.add_line("")

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat."""
        self.chat_history.append({"role": role, "content": content})
        self._update_chat_panel()

    def render(self) -> str:
        """Render the full TUI."""
        self._update_status_panel()
        self._update_chat_panel()
        return self._render_panels()

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="")

    def prompt_input(self) -> str:
        """Show input prompt."""
        prompt = f"{TUIColor.GREEN}> {TUIColor.RESET}"
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return "/quit"

    async def run(self) -> None:
        """Run the TUI main loop."""
        self.running = True

        self.add_message("system", "Welcome to OpenAgent TUI!")
        self.add_message("system", "Type /help for commands")

        self.clear_screen()
        print(self.render())

        while self.running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, self.prompt_input
                )

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                else:
                    # Process as message
                    self.add_message("user", user_input)

                    if self.on_message:
                        response = await self.on_message(user_input)
                        self.add_message("assistant", response)
                    elif self.agent:
                        response = await self.agent.process_message(user_input)
                        self.add_message("assistant", response)

                self.clear_screen()
                print(self.render())

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.add_message("error", f"Error: {str(e)}")

        print(f"\n{TUIColor.YELLOW}Goodbye!{TUIColor.RESET}\n")

    async def _handle_command(self, command: str) -> None:
        """Handle a TUI command."""
        parts = command[1:].split()
        cmd = parts[0].lower() if parts else ""

        if cmd in ["quit", "exit", "q"]:
            self.running = False

        elif cmd in ["help", "h", "?"]:
            self.add_message("system", """
Commands:
  /help, /h       - Show this help
  /quit, /q       - Exit the TUI
  /clear, /c      - Clear chat history
  /sessions, /s   - Show sessions
  /skills, /k     - List skills
  /memory, /m     - Show memory
  /status         - Show status
  /reset          - Reset agent
""")

        elif cmd in ["clear", "c"]:
            self.chat_history = []
            self.add_message("system", "Chat history cleared")

        elif cmd in ["sessions", "s"]:
            if self.gateway:
                sessions = self.gateway.list_sessions()
                self.add_message("system", f"Active sessions: {len(sessions)}")
                for s in sessions:
                    self.add_message("system", f"  - {s.session_id}")
            else:
                self.add_message("system", "No gateway connected")

        elif cmd in ["skills", "k"]:
            if hasattr(self.agent, "skills"):
                for skill in self.agent.skills:
                    self.add_message("system", f"  - {skill.name}: {skill.description}")
            else:
                self.add_message("system", "No skills loaded")

        elif cmd in ["memory", "m"]:
            self.add_message("system", "Use /memory search <query> to search")

        elif cmd in ["status"]:
            self._update_status_panel()
            self.add_message("system", "Status panel updated")

        elif cmd in ["reset"]:
            if self.agent:
                await self.agent.reset("default")
            self.add_message("system", "Agent reset")


async def start_tui(agent: Any = None, gateway: Any = None) -> None:
    """Start the TUI."""
    tui = TUI(agent=agent, gateway=gateway)
    await tui.run()
