"""Core types and interfaces for OpenAgent."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Union, Optional
from pydantic import BaseModel, Field
import time


class PermissionLevel(str, Enum):
    """Permission levels for tools."""
    READ = "read"
    WRITE = "write"
    EXEC = "exec"
    ADMIN = "admin"


class ToolCall(BaseModel):
    """Represents a tool call made by an agent."""
    id: str = Field(default_factory=lambda: f"call_{id(object())}")
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of a tool execution."""
    tool_call_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    id: str
    name: str
    description: Optional[str] = None
    model: str = "nvidia/nemotron"
    system_prompt: Optional[str] = None
    tools: list[str] = Field(default_factory=list)
    max_iterations: int = 10
    timeout: int = 300
    memory_enabled: bool = True
    permission_level: PermissionLevel = PermissionLevel.EXEC


class AgentContext(BaseModel):
    """Context passed to an agent during execution."""
    session_id: str
    user_id: Optional[str] = None
    channel: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A message in a conversation."""
    role: str  # user, assistant, system, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class SessionState(BaseModel):
    """State of an agent session."""
    session_id: str
    agent_id: str
    messages: list[Message] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: time.time())
    last_activity: float = Field(default_factory=lambda: time.time())
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for agents."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent."""
        pass

    @abstractmethod
    async def process_message(self, message: str, context: Optional[AgentContext] = None) -> str:
        """Process a user message and return a response."""
        pass

    @abstractmethod
    async def get_memory(self) -> list[Message]:
        """Get the agent's memory/context."""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset the agent's state."""
        pass
