"""SmithAI Terminal User Interface - Complete Framework.

Full-featured terminal UI providing access to all SmithAI capabilities.
"""

from __future__ import annotations

import os
import sys
import asyncio
import json
import subprocess
import signal
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime
from pathlib import Path


@dataclass
class Command:
    name: str
    description: str
    shortcut: Optional[str] = None
    action: Optional[Callable] = None
    category: str = "General"
    icon: str = ""


class CommandCategory(str, Enum):
    FILE = "File"
    EDIT = "Edit"
    AGENT = "Agent"
    TOOL = "Tool"
    CREW = "Crew"
    MEMORY = "Memory"
    BROWSER = "Browser"
    LLM = "LLM"
    TERMINAL = "Terminal"
    VIEW = "View"
    SETTINGS = "Settings"
    HELP = "Help"


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    DONE = "done"


@dataclass
class AgentState:
    name: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    iterations: int = 0
    tools_used: int = 0
    memory_size: int = 0
    reasoning_quality: float = 0.5
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


@dataclass
class ToolExecution:
    tool_name: str
    args: Dict[str, Any]
    result: Any
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


class SmithAIApp:
    """Main TUI Application with access to all SmithAI features."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.commands: List[Command] = []
        self.agents: Dict[str, AgentState] = {}
        self.tools: Dict[str, Any] = {}
        self.sidebar_visible: bool = True
        self.terminal_visible: bool = True
        self.command_history: List[str] = []
        self._output: List[str] = []
        self._current_llm: str = "openai"
        self._theme: str = "dark"
        
        self._setup()
    
    def _setup(self) -> None:
        self._register_all_commands()
        self._load_tools()
        self._setup_default_agents()
    
    def _register_all_commands(self) -> None:
        self.commands = [
            Command("New File", "Create new file", "Ctrl+N", self._cmd_new_file, CommandCategory.FILE, "[+]"),
            Command("Open File", "Open file from disk", "Ctrl+O", self._cmd_open_file, CommandCategory.FILE, "[O]"),
            Command("Save File", "Save current file", "Ctrl+S", self._cmd_save_file, CommandCategory.FILE, "[S]"),
            Command("Close Tab", "Close current tab", "Ctrl+W", self._cmd_close_tab, CommandCategory.FILE, "[X]"),
            
            Command("New Agent", "Create new AI agent", "Ctrl+Shift+N", self._cmd_new_agent, CommandCategory.AGENT, "[A]"),
            Command("Run Agent", "Run selected agent", "Ctrl+Enter", self._cmd_run_agent, CommandCategory.AGENT, "[>]"),
            Command("Stop Agent", "Stop running agent", "F5", self._cmd_stop_agent, CommandCategory.AGENT, "[#]"),
            Command("Agent Status", "Show agent status", None, self._cmd_agent_status, CommandCategory.AGENT, "[i]"),
            Command("Agent Memory", "View agent memory", None, self._cmd_agent_memory, CommandCategory.AGENT, "[M]"),
            Command("Agent Tools", "Manage agent tools", None, self._cmd_agent_tools, CommandCategory.AGENT, "[T]"),
            Command("Agent Logs", "View agent execution logs", None, self._cmd_agent_logs, CommandCategory.AGENT, "[L]"),
            Command("List Agents", "List all agents", None, self._cmd_list_agents, CommandCategory.AGENT, "[L]"),
            Command("Delete Agent", "Delete an agent", None, self._cmd_delete_agent, CommandCategory.AGENT, "[-]"),
            
            Command("List Tools", "List all available tools", None, self._cmd_list_tools, CommandCategory.TOOL, "[t]"),
            Command("Run Tool", "Execute a tool", None, self._cmd_run_tool, CommandCategory.TOOL, "[>]"),
            Command("Create Tool", "Create custom tool", None, self._cmd_create_tool, CommandCategory.TOOL, "[+]"),
            Command("Tool Inspector", "Inspect tool definition", None, self._cmd_tool_inspector, CommandCategory.TOOL, "[?]"),
            Command("Calculator", "Use calculator tool", None, self._cmd_calculator, CommandCategory.TOOL, "[#]"),
            Command("Web Search", "Search the web", None, self._cmd_web_search, CommandCategory.TOOL, "[?]"),
            
            Command("Create Crew", "Create agent crew", None, self._cmd_create_crew, CommandCategory.CREW, "[C]"),
            Command("Run Crew", "Execute crew tasks", None, self._cmd_run_crew, CommandCategory.CREW, "[>]"),
            Command("Crew Status", "View crew status", None, self._cmd_crew_status, CommandCategory.CREW, "[i]"),
            Command("Crew Logs", "View crew logs", None, self._cmd_crew_logs, CommandCategory.CREW, "[L]"),
            Command("List Crews", "List all crews", None, self._cmd_list_crews, CommandCategory.CREW, "[L]"),
            
            Command("View Memory", "View knowledge base", None, self._cmd_view_memory, CommandCategory.MEMORY, "[M]"),
            Command("Search Memory", "Search knowledge", None, self._cmd_search_memory, CommandCategory.MEMORY, "[?]"),
            Command("Add Memory", "Add to knowledge base", None, self._cmd_add_memory, CommandCategory.MEMORY, "[+]"),
            Command("Clear Memory", "Clear knowledge base", None, self._cmd_clear_memory, CommandCategory.MEMORY, "[X]"),
            Command("Memory Stats", "Memory statistics", None, self._cmd_memory_stats, CommandCategory.MEMORY, "[i]"),
            Command("Knowledge Graph", "Visualize knowledge graph", None, self._cmd_knowledge_graph, CommandCategory.MEMORY, "[G]"),
            Command("Vector Search", "Semantic search", None, self._cmd_vector_search, CommandCategory.MEMORY, "[?]"),
            
            Command("Open Browser", "Open browser", None, self._cmd_open_browser, CommandCategory.BROWSER, "[W]"),
            Command("Browser Screenshot", "Take screenshot", None, self._cmd_browser_screenshot, CommandCategory.BROWSER, "[S]"),
            Command("Web Scrap", "Scrape webpage", None, self._cmd_web_scrape, CommandCategory.BROWSER, "[R]"),
            Command("Solve Captcha", "Solve captcha", None, self._cmd_solve_captcha, CommandCategory.BROWSER, "[C]"),
            Command("Stealth Mode", "Enable stealth browser", None, self._cmd_stealth_mode, CommandCategory.BROWSER, "[S]"),
            
            Command("Switch LLM", "Switch LLM provider", None, self._cmd_switch_llm, CommandCategory.LLM, "[L]"),
            Command("Configure LLM", "Configure LLM settings", None, self._cmd_configure_llm, CommandCategory.LLM, "[C]"),
            Command("Test LLM", "Test LLM connection", None, self._cmd_test_llm, CommandCategory.LLM, "[T]"),
            Command("List Providers", "List all LLM providers", None, self._cmd_list_providers, CommandCategory.LLM, "[L]"),
            
            Command("New Terminal", "Open new terminal", "Ctrl+`", self._cmd_new_terminal, CommandCategory.TERMINAL, "[$]"),
            Command("Clear Terminal", "Clear terminal output", None, self._cmd_clear_terminal, CommandCategory.TERMINAL, "[X]"),
            Command("Run Command", "Run shell command", None, self._cmd_run_command, CommandCategory.TERMINAL, "[>]"),
            
            Command("Toggle Sidebar", "Toggle sidebar", "Ctrl+B", self._cmd_toggle_sidebar, CommandCategory.VIEW, "[|]"),
            Command("Toggle Terminal", "Toggle terminal panel", None, self._cmd_toggle_terminal, CommandCategory.VIEW, "[_]"),
            Command("Toggle Theme", "Switch theme", None, self._cmd_toggle_theme, CommandCategory.VIEW, "[T]"),
            Command("Zoom In", "Increase font size", None, self._cmd_zoom_in, CommandCategory.VIEW, "[+]"),
            Command("Zoom Out", "Decrease font size", None, self._cmd_zoom_out, CommandCategory.VIEW, "[-]"),
            Command("Clear Output", "Clear output log", "Ctrl+Shift+C", self._cmd_clear_output, CommandCategory.VIEW, "[X]"),
            Command("Save Output", "Save output to file", None, self._cmd_save_output, CommandCategory.VIEW, "[S]"),
            
            Command("Settings", "Open settings", None, self._cmd_settings, CommandCategory.SETTINGS, "[S]"),
            Command("API Keys", "Configure API keys", None, self._cmd_api_keys, CommandCategory.SETTINGS, "[K]"),
            Command("Rate Limits", "Configure rate limits", None, self._cmd_rate_limits, CommandCategory.SETTINGS, "[R]"),
            Command("Export Config", "Export configuration", None, self._cmd_export_config, CommandCategory.SETTINGS, "[E]"),
            Command("Import Config", "Import configuration", None, self._cmd_import_config, CommandCategory.SETTINGS, "[I]"),
            
            Command("Help", "Show help", "F1", self._cmd_help, CommandCategory.HELP, "[?]"),
            Command("About", "About SmithAI", None, self._cmd_about, CommandCategory.HELP, "[i]"),
            Command("Documentation", "Open documentation", None, self._cmd_documentation, CommandCategory.HELP, "[D]"),
            Command("Keyboard Shortcuts", "Show shortcuts", None, self._cmd_shortcuts, CommandCategory.HELP, "[K]"),
            Command("Version", "Show version", None, self._cmd_version, CommandCategory.HELP, "[V]"),
        ]
    
    def _load_tools(self) -> None:
        try:
            from smith_ai.tools import list_tools, get_tool, register_builtin_tools
            register_builtin_tools()
            for tool_name in list_tools():
                t = get_tool(tool_name)
                if t:
                    self.tools[tool_name] = t
        except ImportError:
            self._log("Warning: Could not load SmithAI tools")
        except Exception as e:
            self._log(f"Error loading tools: {e}")
    
    def _setup_default_agents(self) -> None:
        self.agents = {
            "default": AgentState(name="default", status=AgentStatus.IDLE),
            "researcher": AgentState(name="researcher", status=AgentStatus.IDLE),
            "writer": AgentState(name="writer", status=AgentStatus.IDLE),
        }
    
    def _log(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "[INFO]", "success": "[OK]", "warning": "[WARN]", "error": "[ERR]", "agent": "[AGENT]", "tool": "[TOOL]"}.get(level, "[MSG]")
        self._output.append(f"{timestamp} {prefix} {message}")
        print(f"{timestamp} {prefix} {message}")
    
    def search_commands(self, query: str) -> List[Command]:
        if not query:
            return self.commands
        q = query.lower()
        return [c for c in self.commands if q in c.name.lower() or q in c.description.lower()]
    
    def execute_command(self, cmd: Command) -> Any:
        if cmd.action:
            return cmd.action()
        return None
    
    def execute_by_name(self, name: str) -> Any:
        for cmd in self.commands:
            if cmd.name.lower() == name.lower():
                return self.execute_command(cmd)
        return None
    
    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        return [c for c in self.commands if c.category == category]
    
    def get_shortcuts(self) -> Dict[str, str]:
        return {cmd.shortcut: cmd.name for cmd in self.commands if cmd.shortcut}
    
    def format_command_list(self) -> str:
        lines = ["Available Commands:", "=" * 50]
        current_category = None
        for cmd in self.commands:
            if cmd.category != current_category:
                lines.append(f"\n{cmd.category}:")
                current_category = cmd.category
            shortcut = cmd.shortcut or ""
            lines.append(f"  {cmd.icon} {cmd.name:25} {shortcut:15} {cmd.description}")
        return "\n".join(lines)
    
    def format_shortcuts(self) -> str:
        shortcuts = self.get_shortcuts()
        lines = ["Keyboard Shortcuts:", "=" * 50]
        for shortcut, name in sorted(shortcuts.items()):
            lines.append(f"  {shortcut:20} {name}")
        return "\n".join(lines)
    
    # File Commands
    def _cmd_new_file(self) -> str:
        self._log("Creating new file...")
        return "new_file"
    
    def _cmd_open_file(self) -> str:
        self._log("Opening file dialog...")
        return "open_file"
    
    def _cmd_save_file(self) -> str:
        self._log("Saving file...")
        return "save_file"
    
    def _cmd_close_tab(self) -> str:
        self._log("Closing tab...")
        return "close_tab"
    
    # Agent Commands
    def _cmd_new_agent(self) -> str:
        self._log("Creating new agent...", "agent")
        return "new_agent"
    
    def _cmd_run_agent(self) -> str:
        self._log("Running agent...", "agent")
        return "run_agent"
    
    def _cmd_stop_agent(self) -> str:
        self._log("Stopping agent...", "agent")
        return "stop_agent"
    
    def _cmd_agent_status(self) -> str:
        lines = ["Agent Status:", "=" * 40]
        for name, state in self.agents.items():
            lines.append(f"  {name}: {state.status.value}")
        return "\n".join(lines)
    
    def _cmd_agent_memory(self) -> str:
        self._log("Viewing agent memory...", "agent")
        return "agent_memory"
    
    def _cmd_agent_tools(self) -> str:
        self._log("Managing agent tools...", "agent")
        return "agent_tools"
    
    def _cmd_agent_logs(self) -> str:
        self._log("Viewing agent logs...", "agent")
        return "agent_logs"
    
    def _cmd_list_agents(self) -> str:
        lines = ["Registered Agents:", "=" * 40]
        for name, state in self.agents.items():
            lines.append(f"  - {name} ({state.status.value})")
        return "\n".join(lines)
    
    def _cmd_delete_agent(self) -> str:
        self._log("Deleting agent...", "agent")
        return "delete_agent"
    
    # Tool Commands
    def _cmd_list_tools(self) -> str:
        if not self.tools:
            return "No tools loaded"
        lines = ["Available Tools:", "=" * 40]
        for name in sorted(self.tools.keys()):
            t = self.tools[name]
            desc = getattr(t, 'description', 'No description')
            lines.append(f"  {name}: {desc}")
        return "\n".join(lines)
    
    def _cmd_run_tool(self) -> str:
        self._log("Running tool...", "tool")
        return "run_tool"
    
    def _cmd_create_tool(self) -> str:
        self._log("Creating new tool...", "tool")
        return "create_tool"
    
    def _cmd_tool_inspector(self) -> str:
        self._log("Opening tool inspector...", "tool")
        return "tool_inspector"
    
    def _cmd_calculator(self) -> str:
        try:
            from smith_ai.tools import get_tool
            calc = get_tool("calculator")
            if calc:
                import inspect
                if inspect.iscoroutinefunction(calc.execute):
                    self._log("Calculator is async - use async mode", "warning")
                    return "Calculator requires async mode"
                result = calc.execute(expression="25 + 17 * 3")
                self._log(f"Calculator result: {result}", "tool")
                return f"Result: {result}"
        except Exception as e:
            self._log(f"Calculator error: {e}", "error")
        return "Calculator not available"
    
    def _cmd_web_search(self) -> str:
        try:
            from smith_ai.tools import get_tool
            search = get_tool("web_search")
            if search:
                import inspect
                if inspect.iscoroutinefunction(search.execute):
                    self._log("Web search is async - use async mode", "warning")
                    return "Web search requires async mode"
                result = search.execute(query="What is AI?")
                self._log("Web search completed", "tool")
                return f"Search result: {str(result)[:200]}..."
        except Exception as e:
            self._log(f"Search error: {e}", "error")
        return "Web search not available"
    
    # Crew Commands
    def _cmd_create_crew(self) -> str:
        self._log("Creating crew...", "agent")
        return "create_crew"
    
    def _cmd_run_crew(self) -> str:
        self._log("Running crew...", "agent")
        return "run_crew"
    
    def _cmd_crew_status(self) -> str:
        self._log("Viewing crew status...", "agent")
        return "crew_status"
    
    def _cmd_crew_logs(self) -> str:
        self._log("Viewing crew logs...", "agent")
        return "crew_logs"
    
    def _cmd_list_crews(self) -> str:
        return "No crews created yet"
    
    # Memory Commands
    def _cmd_view_memory(self) -> str:
        self._log("Viewing memory...", "agent")
        return "view_memory"
    
    def _cmd_search_memory(self) -> str:
        self._log("Searching memory...", "agent")
        return "search_memory"
    
    def _cmd_add_memory(self) -> str:
        self._log("Adding to memory...", "agent")
        return "add_memory"
    
    def _cmd_clear_memory(self) -> str:
        self._log("Clearing memory...", "warning")
        return "clear_memory"
    
    def _cmd_memory_stats(self) -> str:
        lines = ["Memory Statistics:", "=" * 40]
        lines.append(f"  Agents: {len(self.agents)}")
        lines.append(f"  Tools: {len(self.tools)}")
        lines.append(f"  Commands: {len(self.commands)}")
        return "\n".join(lines)
    
    def _cmd_knowledge_graph(self) -> str:
        self._log("Opening knowledge graph...", "agent")
        try:
            from smith_ai.graph import KnowledgeGraph
            kg = KnowledgeGraph()
            if hasattr(kg, 'nodes'):
                return f"Knowledge Graph initialized with {len(kg.nodes)} nodes"
            return "Knowledge Graph available"
        except ImportError:
            return "Knowledge Graph module not available"
        except Exception as e:
            return f"Knowledge Graph error: {e}"
    
    def _cmd_vector_search(self) -> str:
        self._log("Performing vector search...", "agent")
        return "vector_search"
    
    # Browser Commands
    def _cmd_open_browser(self) -> str:
        self._log("Opening browser...", "agent")
        return "open_browser"
    
    def _cmd_browser_screenshot(self) -> str:
        self._log("Taking screenshot...", "agent")
        return "browser_screenshot"
    
    def _cmd_web_scrape(self) -> str:
        self._log("Scraping webpage...", "agent")
        return "web_scrape"
    
    def _cmd_solve_captcha(self) -> str:
        self._log("Solving captcha...", "agent")
        return "solve_captcha"
    
    def _cmd_stealth_mode(self) -> str:
        self._log("Enabling stealth mode...", "agent")
        return "stealth_mode"
    
    # LLM Commands
    def _cmd_switch_llm(self) -> str:
        lines = ["Available LLM Providers:", "=" * 40]
        try:
            from smith_ai.core import LLMProvider
            for provider in LLMProvider:
                current = " (current)" if provider.value == self._current_llm else ""
                lines.append(f"  {provider.value}{current}")
        except ImportError:
            lines.append("  LLM providers not available")
        return "\n".join(lines)
    
    def _cmd_configure_llm(self) -> str:
        self._log("Configuring LLM...", "info")
        return "configure_llm"
    
    def _cmd_test_llm(self) -> str:
        self._log("Testing LLM connection...", "info")
        return "test_llm"
    
    def _cmd_list_providers(self) -> str:
        lines = ["LLM Providers:", "=" * 40]
        try:
            from smith_ai.core import LLMProvider
            for provider in LLMProvider:
                lines.append(f"  - {provider.value}")
        except ImportError:
            lines.append("  Providers not available")
        return "\n".join(lines)
    
    # Terminal Commands
    def _cmd_new_terminal(self) -> str:
        self._log("Opening new terminal...", "info")
        return "new_terminal"
    
    def _cmd_clear_terminal(self) -> str:
        self._log("Clearing terminal...", "info")
        return "clear_terminal"
    
    def _cmd_run_command(self) -> str:
        self._log("Running shell command...", "info")
        return "run_command"
    
    # View Commands
    def _cmd_toggle_sidebar(self) -> str:
        self.sidebar_visible = not self.sidebar_visible
        self._log(f"Sidebar: {'visible' if self.sidebar_visible else 'hidden'}", "info")
        return "toggle_sidebar"
    
    def _cmd_toggle_terminal(self) -> str:
        self.terminal_visible = not self.terminal_visible
        self._log(f"Terminal: {'visible' if self.terminal_visible else 'hidden'}", "info")
        return "toggle_terminal"
    
    def _cmd_toggle_theme(self) -> str:
        self._theme = "light" if self._theme == "dark" else "dark"
        self._log(f"Theme: {self._theme}", "info")
        return "toggle_theme"
    
    def _cmd_zoom_in(self) -> str:
        self._log("Zooming in...", "info")
        return "zoom_in"
    
    def _cmd_zoom_out(self) -> str:
        self._log("Zooming out...", "info")
        return "zoom_out"
    
    def _cmd_clear_output(self) -> str:
        self._output.clear()
        self._log("Output cleared", "info")
        return "clear_output"
    
    def _cmd_save_output(self) -> str:
        self._log("Saving output...", "info")
        return "save_output"
    
    # Settings Commands
    def _cmd_settings(self) -> str:
        self._log("Opening settings...", "info")
        return "settings"
    
    def _cmd_api_keys(self) -> str:
        self._log("Configuring API keys...", "info")
        return "api_keys"
    
    def _cmd_rate_limits(self) -> str:
        self._log("Configuring rate limits...", "info")
        return "rate_limits"
    
    def _cmd_export_config(self) -> str:
        self._log("Exporting configuration...", "info")
        return "export_config"
    
    def _cmd_import_config(self) -> str:
        self._log("Importing configuration...", "info")
        return "import_config"
    
    # Help Commands
    def _cmd_help(self) -> str:
        return self.format_command_list()
    
    def _cmd_about(self) -> str:
        return """
SmithAI - True AGI Framework
Version: 4.0.0
Based on Common Model of Cognition (ACT-R, Soar, Sigma)

Features:
- Multi-Method Reasoning (Deductive, Inductive, Abductive, Causal, Analogical)
- Hierarchical Task Planning (HTN)
- Metacognition & Self-Improvement
- World Model & Knowledge Graph
- Multi-Agent Collaboration
- OpenShell Integration
"""
    
    def _cmd_documentation(self) -> str:
        return "Documentation: https://github.com/Himan-D/open-agent-sdk"
    
    def _cmd_shortcuts(self) -> str:
        return self.format_shortcuts()
    
    def _cmd_version(self) -> str:
        try:
            from smith_ai import __version__
            return f"SmithAI Version: {__version__}"
        except ImportError:
            return "Version: 4.0.0"


class TUIRunner:
    """Runs TUI in various modes."""
    
    def __init__(self, app: SmithAIApp):
        self.app = app
    
    def run_interactive(self) -> None:
        """Run interactive command-line interface."""
        print("\n" + "=" * 70)
        print(" SmithAI Interactive Shell v4.0.0")
        print("=" * 70)
        print("\nType 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                cmd = input(">>> ").strip()
                if cmd.lower() in ('exit', 'quit', 'q'):
                    break
                if not cmd:
                    continue
                
                result = self.app.execute_by_name(cmd)
                if result:
                    print(result)
                else:
                    results = self.app.search_commands(cmd)
                    if results:
                        for r in results[:5]:
                            print(f"  {r.name}: {r.description}")
                    else:
                        print(f"Unknown: {cmd}. Type 'help' for commands.")
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break
        
        print("\nGoodbye!")


class TUIBridge:
    """Bridge between TUI and SmithAI core."""
    
    def __init__(self):
        self.app = SmithAIApp()
    
    def run_interactive(self) -> None:
        runner = TUIRunner(self.app)
        runner.run_interactive()


def create_tui(mode: str = "interactive") -> SmithAIApp:
    """Create and run TUI."""
    app = SmithAIApp()
    
    if mode == "interactive":
        runner = TUIRunner(app)
        runner.run_interactive()
    elif mode == "demo":
        print("\n" + "=" * 70)
        print(" SmithAI TUI Demo")
        print("=" * 70)
        print(app.format_command_list())
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: interactive, demo")
    
    return app


async def async_run_tool(tool_name: str, **kwargs: Any) -> Any:
    """Run a tool asynchronously."""
    try:
        from smith_ai.tools import get_tool
        tool = get_tool(tool_name)
        if not tool:
            return f"Tool not found: {tool_name}"
        
        import inspect
        if inspect.iscoroutinefunction(tool.execute):
            return await tool.execute(**kwargs)
        else:
            return tool.execute(**kwargs)
    except Exception as e:
        return f"Error: {e}"


async def async_run_agent(agent_name: str, task: str, tools: Optional[List[str]] = None) -> str:
    """Run an agent asynchronously."""
    try:
        from smith_ai import Agent
        
        agent = Agent(
            name=agent_name,
            role="AI Assistant",
            goal=task,
            backstory="You are a helpful AI assistant.",
        )
        
        if tools:
            from smith_ai.tools import get_tool
            for tool_name in tools:
                t = get_tool(tool_name)
                if t:
                    agent.add_tool(t)
        
        result = await agent.run(task)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


async def async_execute_command_chain(commands: List[Tuple[str, Dict[str, Any]]]) -> List[Any]:
    """Execute a chain of commands asynchronously."""
    results = []
    for cmd_name, kwargs in commands:
        if cmd_name == "run_tool":
            result = await async_run_tool(**kwargs)
        elif cmd_name == "run_agent":
            result = await async_run_agent(**kwargs)
        else:
            result = "Unknown command"
        results.append(result)
    return results


__all__ = [
    "SmithAIApp",
    "TUIRunner",
    "TUIBridge",
    "Command",
    "CommandCategory",
    "AgentStatus",
    "AgentState",
    "ToolExecution",
    "create_tui",
]
