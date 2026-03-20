"""OpenClaw-style orchestration layer for deep agents.

This module implements an OpenClaw-inspired architecture with:
- Gateway for message routing and session management
- Agent harness with planning, memory, and tool execution
- Multi-agent support with hierarchy and delegation
- Skills system for extensibility
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import structlog

from open_agent.config.settings import get_config, AgentConfig, MemoryConfig
from open_agent.models.nemotron import create_nemotron_model, NemotronModel
from open_agent.backends.openshell import OpenShellBackend, SandboxSession

logger = structlog.get_logger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels for agent actions."""
    READ = "read"
    WRITE = "write"
    EXEC = "exec"
    ADMIN = "admin"


@dataclass
class AgentContext:
    """Context for agent execution."""
    session_id: str
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """A message in agent conversation."""
    role: str  # user, assistant, system, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ToolCall:
    """A tool call made by an agent."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_call_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Skill:
    """A skill that can be loaded by the agent."""
    name: str
    description: str
    instructions: str
    file_path: Optional[str] = None


@dataclass
class SoulConfig:
    """OpenClaw-style SOUL.md configuration for an agent."""
    name: str
    emoji: str = ""
    team: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    reporting_to: Optional[str] = None
    work_style: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    custom_instructions: str = ""


class BaseTool:
    """Base class for agent tools."""

    def __init__(
        self,
        name: str,
        description: str,
        permission_level: PermissionLevel = PermissionLevel.EXEC,
    ):
        self.name = name
        self.description = description
        self.permission_level = permission_level

    async def execute(self, **kwargs) -> str:
        """Execute the tool."""
        raise NotImplementedError


class ShellTool(BaseTool):
    """Tool for shell command execution via OpenShell."""

    def __init__(self, backend: Optional[OpenShellBackend] = None):
        super().__init__(
            name="execute",
            description="Execute a shell command in the sandbox",
            permission_level=PermissionLevel.EXEC,
        )
        self.backend = backend or OpenShellBackend()
        self.session: Optional[SandboxSession] = None

    async def execute(self, command: str, **kwargs) -> str:
        """Execute a shell command."""
        if self.session is None:
            self.session = self.backend.create_sandbox("nemotron")

        result = self.session.exec(command)
        if result["success"]:
            return result["stdout"]
        else:
            return f"Error: {result.get('stderr', 'Unknown error')}"


class FileTools(BaseTool):
    """File system tools (ls, read, write, edit)."""

    def __init__(self, backend: Optional[OpenShellBackend] = None):
        super().__init__(
            name="filesystem",
            description="File system operations",
            permission_level=PermissionLevel.WRITE,
        )
        self.backend = backend or OpenShellBackend()
        self.session: Optional[SandboxSession] = None

    async def ls(self, path: str = ".") -> str:
        """List directory contents."""
        if self.session is None:
            self.session = self.backend.create_sandbox("nemotron")
        return self.session.exec(f"ls -la {path}")["stdout"]

    async def read_file(self, path: str) -> str:
        """Read a file."""
        if self.session is None:
            self.session = self.backend.create_sandbox("nemotron")
        return self.session.read_file(path)

    async def write_file(self, path: str, content: str) -> str:
        """Write a file."""
        if self.session is None:
            self.session = self.backend.create_sandbox("nemotron")
        result = self.session.write_file(path, content)
        return "File written successfully" if result["success"] else f"Error: {result.get('error')}"

    async def edit_file(self, path: str, old_text: str, new_text: str) -> str:
        """Edit a file (replace old_text with new_text)."""
        content = await self.read_file(path)
        content = content.replace(old_text, new_text)
        return await self.write_file(path, content)


class TodoTool(BaseTool):
    """Todo list tool for planning and task tracking."""

    def __init__(self):
        super().__init__(
            name="todo",
            description="Track and manage todo items for complex tasks",
            permission_level=PermissionLevel.WRITE,
        )
        self.todos: List[Dict[str, Any]] = []

    async def write_todos(self, todos: List[Dict[str, Any]]) -> str:
        """Write/update todo list."""
        self.todos = todos
        return f"Updated {len(todos)} todo items"

    async def complete_todo(self, todo_id: str) -> str:
        """Mark a todo as complete."""
        for todo in self.todos:
            if todo.get("id") == todo_id:
                todo["status"] = "complete"
                return f"Marked todo '{todo.get('content', todo_id)}' as complete"
        return f"Todo '{todo_id}' not found"

    async def get_todos(self) -> List[Dict[str, Any]]:
        """Get current todo list."""
        return self.todos


class DeepAgent:
    """Deep Agent powered by LangChain, Nemotron, and OpenShell.

    This is the core agent harness that combines:
    - NVIDIA Nemotron for reasoning
    - LangGraph for agentic loop
    - OpenShell for secure execution
    - Memory and skills for persistence
    """

    def __init__(
        self,
        name: str = "deep-agent",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        skills: Optional[List[Skill]] = None,
        soul: Optional[SoulConfig] = None,
        openshell_backend: Optional[OpenShellBackend] = None,
        memory_enabled: bool = True,
        max_iterations: int = 50,
    ):
        self.app_config = get_config()
        self.name = name
        self.soul = soul
        self.tools = tools or []
        self.skills = skills or []
        self.openshell_backend = openshell_backend
        self.memory_enabled = memory_enabled
        self.max_iterations = max_iterations
        self._base_system_prompt = system_prompt

        # Initialize model
        self.nemotron = create_nemotron_model(
            model_name=model or self.app_config.agent_config.model,
            temperature=self.app_config.agent_config.temperature,
        )

        # Session state
        self.sessions: Dict[str, List[Message]] = {}
        self.current_todos: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("deep_agent_initialized", name=name, model=model)

        # Initialize model
        self.nemotron = create_nemotron_model(
            model_name=model or self.app_config.agent_config.model,
            temperature=self.app_config.agent_config.temperature,
        )

        # Session state
        self.sessions: Dict[str, List[Message]] = {}
        self.current_todos: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("deep_agent_initialized", name=name, model=model)

    def _build_system_prompt(self) -> str:
        """Build the system prompt from soul config."""
        parts = []

        if self.soul:
            parts.append(f"# {self.soul.emoji} {self.soul.name}\n")
            if self.soul.team:
                parts.append(f"Team: {self.soul.team}\n")
            if self.soul.responsibilities:
                parts.append("## Responsibilities\n")
                for resp in self.soul.responsibilities:
                    parts.append(f"- {resp}\n")
            if self.soul.constraints:
                parts.append("## Constraints\n")
                for constraint in self.soul.constraints:
                    parts.append(f"- {constraint}\n")

        parts.append("## Instructions\n")
        parts.append(self._base_system_prompt or "You are a helpful AI assistant.")

        if self.tools:
            parts.append("\n## Available Tools\n")
            for tool in self.tools:
                parts.append(f"- **{tool.name}**: {tool.description}\n")

        return "".join(parts)

    async def initialize(self) -> None:
        """Initialize the agent."""
        if self.openshell_backend:
            self.openshell_backend.initialize()

        for skill in self.skills:
            logger.info("skill_loaded", skill_name=skill.name)

        logger.info("agent_ready", name=self.name)

    async def process_message(
        self,
        message: str,
        context: Optional[AgentContext] = None,
    ) -> str:
        """Process a user message and return a response."""
        session_id = context.session_id if context else "default"
        thread_id = context.thread_id if context else "main"

        # Get or create session
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        # Add user message
        self.sessions[session_id].append(Message(role="user", content=message))

        # Build messages for LLM
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        messages = [SystemMessage(content=self._build_system_prompt())]

        for msg in self.sessions[session_id][-20:]:  # Last 20 messages
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))

        # Invoke model
        try:
            response = await self.nemotron.ainvoke(messages)
            response_content = response.content
        except Exception as e:
            logger.error("model_invoke_error", error=str(e))
            response_content = f"I encountered an error: {str(e)}"

        # Add response to session
        self.sessions[session_id].append(Message(role="assistant", content=response_content))

        return response_content

    async def spawn_subagent(
        self,
        name: str,
        task: str,
        parent_session: Optional[str] = None,
    ) -> "DeepAgent":
        """Spawn a subagent for delegated tasks."""
        subagent = DeepAgent(
            name=name,
            system_prompt=f"You are {name}, a specialized subagent. Your task: {task}",
            tools=self.tools,
            openshell_backend=self.openshell_backend,
            memory_enabled=False,  # Subagents don't persist memory
        )
        await subagent.initialize()
        return subagent

    def get_memory(self, session_id: str) -> List[Message]:
        """Get session memory."""
        return self.sessions.get(session_id, [])

    async def reset(self, session_id: str) -> None:
        """Reset agent session."""
        if session_id in self.sessions:
            self.sessions[session_id] = []
        if session_id in self.current_todos:
            del self.current_todos[session_id]
        logger.info("session_reset", session_id=session_id)

    def load_skill(self, skill: Skill) -> None:
        """Load a skill into the agent."""
        self.skills.append(skill)
        logger.info("skill_loaded", skill_name=skill.name)


def create_deep_agent(
    name: str = "deep-agent",
    model: str = "nvidia/nemotron-3-super-120b-a12b",
    system_prompt: Optional[str] = None,
    tools: Optional[List[BaseTool]] = None,
    skills: Optional[List[Skill]] = None,
    soul: Optional[SoulConfig] = None,
    use_openshell: bool = True,
    memory_enabled: bool = True,
) -> DeepAgent:
    """Create a configured deep agent.

    Example:
        >>> from open_agent.orchestration.openclaw import create_deep_agent, ShellTool
        >>>
        >>> agent = create_deep_agent(
        ...     name="coding-agent",
        ...     model="nvidia/nemotron-3-super-120b-a12b",
        ...     tools=[ShellTool()],
        ...     system_prompt="You are a coding assistant."
        ... )
    """
    openshell_backend = None
    if use_openshell:
        try:
            openshell_backend = OpenShellBackend()
        except Exception as e:
            logger.warning("openshell_not_available", error=str(e))

    agent_tools = tools or []
    if use_openshell and openshell_backend:
        agent_tools.append(ShellTool(openshell_backend))
        agent_tools.append(FileTools(openshell_backend))

    # Add todo tool
    agent_tools.append(TodoTool())

    return DeepAgent(
        name=name,
        model=model,
        system_prompt=system_prompt,
        tools=agent_tools,
        skills=skills,
        soul=soul,
        openshell_backend=openshell_backend,
        memory_enabled=memory_enabled,
    )
