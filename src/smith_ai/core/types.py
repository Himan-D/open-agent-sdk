"""Core types and interfaces for SmithAI.

Single source of truth for all shared types.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"
    AZURE = "azure"
    MISTRAL = "mistral"
    COHERE = "cohere"
    OPENROUTER = "openrouter"


class Process(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    EXEC = "exec"
    ADMIN = "admin"


@dataclass
class AgentMessage:
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentMessage:
        return cls(
            role=data["role"],
            content=data["content"],
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class ToolCall:
    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex[:8]}")
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class ToolResult:
    tool_call_id: str
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass 
class ToolSchema:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    examples: List[str] = field(default_factory=list)
    
    def to_openai_format(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    streaming: bool = True
    
    @classmethod
    def from_env(cls, provider: LLMProvider) -> LLMConfig:
        import os
        env_prefix = provider.value.upper()
        return cls(
            provider=provider,
            model=os.getenv(f"{env_prefix}_MODEL", ""),
            api_key=os.getenv(f"{env_prefix}_API_KEY"),
            base_url=os.getenv(f"{env_prefix}_BASE_URL"),
        )


@dataclass
class AgentConfig:
    name: str
    role: str
    goal: str
    backstory: str = ""
    llm_config: Optional[LLMConfig] = None
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 10
    verbose: bool = False
    
    def __post_init__(self):
        if not self.backstory:
            self.backstory = f"You are {self.name}, a {self.role}."


@dataclass
class TaskConfig:
    description: str
    agent_name: str
    expected_output: str = ""
    async_execution: bool = False


@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Synchronous invoke."""
        pass
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Asynchronous invoke."""
        pass


class BaseTool(ABC):
    """Abstract base class for tools."""
    
    name: str = "base_tool"
    description: str = "A base tool"
    category: str = "general"
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool asynchronously."""
        pass
    
    def get_schema(self) -> ToolSchema:
        """Get the tool's schema for LLM function calling."""
        return ToolSchema(
            name=self.name,
            description=self.description,
            category=self.category,
        )


class BaseAgent(ABC):
    """Abstract base class for agents."""
    
    @abstractmethod
    async def run(self, task: str) -> ExecutionResult:
        """Run a task with the agent."""
        pass
    
    @abstractmethod
    async def reset(self) -> None:
        """Reset the agent's state."""
        pass
