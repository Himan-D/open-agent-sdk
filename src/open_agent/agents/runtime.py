"""Agent runtime - Core agent execution engine."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import time
import structlog

from open_agent.agents.tools.base import BaseTool, ToolResult, ToolCall
from open_agent.agents.tools.shell import ShellTool
from open_agent.agents.tools.filesystem import FileTools
from open_agent.agents.tools.todo import TodoTool
from open_agent.agents.skills.registry import Skill
from open_agent.agents.sandbox.backend import OpenShellBackend
from open_agent.providers.nemotron import create_nemotron_model

logger = structlog.get_logger(__name__)


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
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


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
        self.name = name
        self.soul = soul
        self.tools = tools or []
        self.skills = skills or []
        self.openshell_backend = openshell_backend
        self.memory_enabled = memory_enabled
        self.max_iterations = max_iterations
        self._base_system_prompt = system_prompt
        self.model_name = model or "nvidia/nemotron-3-super-120b-a12b"

        self.nemotron = create_nemotron_model(
            model_name=self.model_name,
            temperature=0.7,
        )

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

        if session_id not in self.sessions:
            self.sessions[session_id] = []

        self.sessions[session_id].append(Message(role="user", content=message))

        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        messages = [SystemMessage(content=self._build_system_prompt())]

        for msg in self.sessions[session_id][-20:]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                if isinstance(msg.content, str):
                    messages.append(AIMessage(content=msg.content))

        try:
            response = await self.nemotron.ainvoke(messages)
            response_content = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error("model_invoke_error", error=str(e))
            response_content = f"I encountered an error: {str(e)}"

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
            memory_enabled=False,
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
    """Create a configured deep agent."""
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
