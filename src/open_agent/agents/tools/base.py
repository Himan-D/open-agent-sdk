"""Base tool classes for agent tool system."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time


class PermissionLevel(str, Enum):
    """Permission levels for agent actions."""
    READ = "read"
    WRITE = "write"
    EXEC = "exec"
    ADMIN = "admin"


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
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool:
    """Base class for agent tools.
    
    Tools are the primary way for agents to interact with the outside world.
    They provide capabilities like shell execution, file operations, and
    integration with external services.
    
    Example:
        >>> class MyTool(BaseTool):
        ...     def __init__(self):
        ...         super().__init__(
        ...             name="my_tool",
        ...             description="Does something useful",
        ...             permission_level=PermissionLevel.EXEC,
        ...         )
        ...
        ...     async def execute(self, **kwargs) -> str:
        ...         return "Result"
    """

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
        """Execute the tool with the given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            Tool execution result as a string
        """
        raise NotImplementedError

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool's parameters."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }


class ToolRegistry:
    """Registry for managing agent tools."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list(self) -> List[BaseTool]:
        """List all registered tools."""
        return list(self.tools.values())

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(
                tool_call_id=kwargs.get("tool_call_id", ""),
                success=False,
                error=f"Tool '{tool_name}' not found",
            )

        try:
            output = await tool.execute(**kwargs)
            return ToolResult(
                tool_call_id=kwargs.get("tool_call_id", ""),
                success=True,
                output=output,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=kwargs.get("tool_call_id", ""),
                success=False,
                error=str(e),
            )
