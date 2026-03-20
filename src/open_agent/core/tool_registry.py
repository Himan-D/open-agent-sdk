"""Tool registry and tool base class."""

from typing import Any, Callable
from pydantic import BaseModel, Field
import structlog

from open_agent.core.types import ToolCall, ToolResult, PermissionLevel

logger = structlog.get_logger(__name__)


class Tool(BaseModel):
    """Base tool definition."""
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.EXEC
    is_async: bool = True

    def execute(self, **kwargs) -> Any:
        """Execute the tool synchronously."""
        raise NotImplementedError

    async def aexecute(self, **kwargs) -> Any:
        """Execute the tool asynchronously."""
        return self.execute(**kwargs)


class ToolMetadata(BaseModel):
    """Metadata about a registered tool."""
    name: str
    description: str
    permission_level: PermissionLevel
    is_async: bool


class ToolRegistry:
    """Registry for managing and accessing tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._permissions: dict[str, PermissionLevel] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        self._permissions[tool.name] = tool.permission_level
        logger.info("tool_registered", tool_name=tool.name)

    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            del self._permissions[name]
            logger.info("tool_unregistered", tool_name=name)
            return True
        return False

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list(self) -> list[ToolMetadata]:
        """List all registered tools."""
        return [
            ToolMetadata(
                name=name,
                description=tool.description,
                permission_level=tool.permission_level,
                is_async=tool.is_async,
            )
            for name, tool in self._tools.items()
        ]

    def check_permission(self, name: str, required_level: PermissionLevel) -> bool:
        """Check if a tool has the required permission level."""
        tool_level = self._permissions.get(name)
        if not tool_level:
            return False
        levels = list(PermissionLevel)
        return levels.index(tool_level) >= levels.index(required_level)

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                tool_call_id="",
                success=False,
                error=f"Tool '{name}' not found",
            )

        tool_call_id = f"call_{id(tool)}"
        try:
            if tool.is_async:
                result = await tool.aexecute(**arguments)
            else:
                result = tool.execute(**arguments)
            return ToolResult(
                tool_call_id=tool_call_id,
                success=True,
                output=str(result),
            )
        except Exception as e:
            logger.error("tool_execution_failed", tool_name=name, error=str(e))
            return ToolResult(
                tool_call_id=tool_call_id,
                success=False,
                error=str(e),
            )

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools


# Global default registry
default_registry = ToolRegistry()
