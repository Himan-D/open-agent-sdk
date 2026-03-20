"""Todo tool for planning and task tracking."""

from typing import List, Dict, Any
from open_agent.agents.tools.base import BaseTool, PermissionLevel
import structlog

logger = structlog.get_logger(__name__)


class TodoTool(BaseTool):
    """Todo list tool for planning and task tracking.
    
    Provides task management capabilities for complex multi-step tasks,
    similar to OpenClaw's todo tool.
    
    Example:
        >>> tool = TodoTool()
        >>> await tool.write_todos([
        ...     {"id": "1", "content": "Task 1", "status": "pending"},
        ...     {"id": "2", "content": "Task 2", "status": "pending"},
        ... ])
        >>> todos = await tool.get_todos()
    """

    def __init__(self):
        super().__init__(
            name="todo",
            description="Track and manage todo items for complex tasks",
            permission_level=PermissionLevel.WRITE,
        )
        self.todos: List[Dict[str, Any]] = []

    async def execute(self, action: str, **kwargs) -> str:
        """Execute a todo action.
        
        Args:
            action: Action to perform (get, write, complete)
            **kwargs: Action-specific arguments
            
        Returns:
            Action result
        """
        if action == "get":
            return str(await self.get_todos())
        elif action == "write":
            todos = kwargs.get("todos", [])
            return await self.write_todos(todos)
        elif action == "complete":
            todo_id = kwargs.get("todo_id", "")
            return await self.complete_todo(todo_id)
        else:
            return f"Unknown action: {action}"

    async def write_todos(self, todos: List[Dict[str, Any]]) -> str:
        """Write/update todo list.
        
        Args:
            todos: List of todo items
            
        Returns:
            Status message
        """
        self.todos = todos
        return f"Updated {len(todos)} todo items"

    async def complete_todo(self, todo_id: str) -> str:
        """Mark a todo as complete.
        
        Args:
            todo_id: ID of the todo to complete
            
        Returns:
            Status message
        """
        for todo in self.todos:
            if todo.get("id") == todo_id:
                todo["status"] = "complete"
                return f"Marked todo '{todo.get('content', todo_id)}' as complete"
        return f"Todo '{todo_id}' not found"

    async def get_todos(self) -> List[Dict[str, Any]]:
        """Get current todo list.
        
        Returns:
            List of todo items
        """
        return self.todos
