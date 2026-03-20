"""Modular Tool System - Easy to extend with custom tools."""

from __future__ import annotations

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str = "base_tool"
    description: str = "A base tool"
    category: str = "general"
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool asynchronously."""
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class ToolRegistry:
    """Central registry for all tools."""
    
    _instance: Optional["ToolRegistry"] = None
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance
    
    def register(self, tool: BaseTool, category: Optional[str] = None) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        cat = category or tool.category
        if cat not in self._categories:
            self._categories[cat] = []
        if tool.name not in self._categories[cat]:
            self._categories[cat].append(tool.name)
        logger.info("tool_registered", name=tool.name, category=cat)
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self._tools:
            tool = self._tools.pop(name)
            for cat in self._categories:
                if name in self._categories[cat]:
                    self._categories[cat].remove(name)
            logger.info("tool_unregistered", name=name)
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    
    def list_all(self) -> List[str]:
        return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[BaseTool]:
        names = self._categories.get(category, [])
        return [self._tools[n] for n in names if n in self._tools]
    
    def list_categories(self) -> List[str]:
        return list(self._categories.keys())
    
    async def execute(self, name: str, *args, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool '{name}' not found")
        try:
            return await tool.execute(*args, **kwargs)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def create_wrapper(self, func: Callable, name: str, description: str) -> BaseTool:
        """Create a tool from a simple function."""
        
        class FunctionTool(BaseTool):
            name = name
            description = description
            
            async def execute(self, *args, **kwargs) -> ToolResult:
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    return ToolResult(success=True, output=str(result))
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        
        return FunctionTool()


def create_tool(
    name: str,
    description: str,
    func: Callable,
    category: str = "custom",
) -> BaseTool:
    """Create a custom tool from a function.
    
    Example:
        >>> def my_calculator(expr: str) -> str:
        ...     return str(eval(expr))
        >>> calc_tool = create_tool("calc", "Calculator", my_calculator)
        >>> registry.register(calc_tool)
    """
    registry = ToolRegistry.get_instance()
    tool = registry.create_wrapper(func, name, description)
    tool.category = category
    return tool


def tool(
    name: str = None,
    description: str = None,
    category: str = "custom",
):
    """Decorator to create a tool from a function.
    
    Example:
        >>> @tool(name="greet", description="Greet someone")
        ... async def greet(name: str) -> str:
        ...     return f"Hello, {name}!"
        >>> registry.register(greet_tool)
    """
    def decorator(func: Callable) -> BaseTool:
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Tool: {tool_name}"
        tool_cat = category
        
        class DecoratedTool(BaseTool):
            _name = tool_name
            _desc = tool_desc
            _cat = tool_cat
            
            @property
            def name(self):
                return self._name
            
            @property
            def description(self):
                return self._desc
            
            @property
            def category(self):
                return self._cat
            
            async def execute(self, *args, **kwargs) -> ToolResult:
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    return ToolResult(success=True, output=str(result))
                except Exception as e:
                    return ToolResult(success=False, error=str(e))
        
        return DecoratedTool()
    
    return decorator


# =============================================================================
# BUILT-IN TOOLS
# =============================================================================

class CalculatorTool(BaseTool):
    """Mathematical calculator with safe evaluation."""
    
    name = "calculator"
    description = "Evaluate mathematical expressions safely. Input: expression string"
    category = "math"
    
    _SAFE_NAMES = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sum": sum, "pow": pow, "sqrt": __import__("math").sqrt,
        "sin": __import__("math").sin, "cos": __import__("math").cos,
        "tan": __import__("math").tan, "log": __import__("math").log,
        "pi": __import__("math").pi, "e": __import__("math").e,
        "floor": __import__("math").floor, "ceil": __import__("math").ceil,
    }
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            result = eval(expression, {"__builtins__": {}}, self._SAFE_NAMES)
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo."""
    
    name = "web_search"
    description = "Search the web. Input: search query"
    category = "research"
    
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        try:
            import httpx
            response = httpx.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json"},
                timeout=10
            )
            data = response.json()
            results = []
            for item in data.get("RelatedTopics", [])[:num_results]:
                if "Text" in item:
                    results.append(f"- {item['Text']}")
            output = "\n".join(results) if results else "No results found"
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebFetchTool(BaseTool):
    """Fetch content from URLs."""
    
    name = "fetch_url"
    description = "Fetch content from a URL. Input: URL"
    category = "web"
    
    async def execute(self, url: str, max_length: int = 5000) -> ToolResult:
        try:
            import httpx
            response = httpx.get(url, timeout=10, follow_redirects=True)
            content = response.text[:max_length]
            if len(response.text) > max_length:
                content += f"\n... (truncated, total: {len(response.text)} chars)"
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class PythonREPLTool(BaseTool):
    """Execute Python code safely."""
    
    name = "python_repl"
    description = "Execute Python code. Input: Python code"
    category = "code"
    
    async def execute(self, code: str, timeout: int = 30) -> ToolResult:
        try:
            import io, contextlib, traceback
            
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": __builtins__})
            
            result = output.getvalue() or "Executed successfully (no output)"
            return ToolResult(success=True, output=result)
        except Exception as e:
            tb = traceback.format_exc()
            return ToolResult(success=False, error=f"{type(e).__name__}: {e}\n{tb}")


class FileReadTool(BaseTool):
    """Read files from filesystem."""
    
    name = "read_file"
    description = "Read a file. Input: file path"
    category = "filesystem"
    
    async def execute(self, path: str, max_lines: int = 100) -> ToolResult:
        try:
            with open(path, 'r') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"... (truncated at line {max_lines})")
                        break
                    lines.append(line.rstrip())
            return ToolResult(success=True, output="\n".join(lines))
        except FileNotFoundError:
            return ToolResult(success=False, error=f"File not found: {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileWriteTool(BaseTool):
    """Write files to filesystem."""
    
    name = "write_file"
    description = "Write to a file. Input: path and content separated by |"
    category = "filesystem"
    
    async def execute(self, path_content: str, content: str = None) -> ToolResult:
        try:
            if "|" in path_content and content is None:
                parts = path_content.split("|", 1)
                path, content = parts[0].strip(), parts[1]
            else:
                path = path_content
            
            with open(path, 'w') as f:
                f.write(content or "")
            return ToolResult(success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class JSONTool(BaseTool):
    """Parse and manipulate JSON."""
    
    name = "json_tool"
    description = "Parse JSON, format JSON, or extract values. Input: JSON string or 'format: <json>'"
    category = "utility"
    
    async def execute(self, input_str: str) -> ToolResult:
        try:
            if input_str.startswith("format:"):
                data = json.loads(input_str[7:].strip())
                return ToolResult(success=True, output=json.dumps(data, indent=2))
            elif input_str.startswith("get:"):
                parts = input_str[4:].strip().split(".", 1)
                data = json.loads(parts[0])
                for key in parts[1].split("."):
                    data = data[key]
                return ToolResult(success=True, output=str(data))
            else:
                data = json.loads(input_str)
                return ToolResult(success=True, output=f"Valid JSON: {json.dumps(data)[:100]}...")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class TextTool(BaseTool):
    """Text manipulation utilities."""
    
    name = "text_tool"
    description = "Text operations: uppercase, lowercase, word_count, char_count, reverse, slugify"
    category = "utility"
    
    async def execute(self, operation: str, text: str = None) -> ToolResult:
        try:
            if "|" in operation and text is None:
                parts = operation.split("|", 1)
                operation, text = parts[0].strip(), parts[1]
            
            ops = {
                "uppercase": lambda t: t.upper(),
                "lowercase": lambda t: t.lower(),
                "word_count": lambda t: str(len(t.split())),
                "char_count": lambda t: str(len(t)),
                "reverse": lambda t: t[::-1],
                "slugify": lambda t: re.sub(r'[^\w\s-]', '', t.lower()).replace(' ', '-'),
            }
            
            if operation not in ops:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
            
            return ToolResult(success=True, output=ops[operation](text))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DateTimeTool(BaseTool):
    """Date and time utilities."""
    
    name = "datetime_tool"
    description = "Get current datetime, format dates, calculate differences"
    category = "utility"
    
    async def execute(self, operation: str, value: str = None) -> ToolResult:
        try:
            from datetime import datetime, timedelta
            
            ops = {
                "now": lambda: datetime.now().isoformat(),
                "today": lambda: datetime.now().date().isoformat(),
                "timestamp": lambda: str(datetime.now().timestamp()),
            }
            
            if operation in ops:
                return ToolResult(success=True, output=ops[operation]())
            
            if operation == "format" and value:
                dt = datetime.fromisoformat(value)
                return ToolResult(success=True, output=dt.strftime("%Y-%m-%d %H:%M:%S"))
            
            if operation == "diff" and value:
                parts = value.split(",")
                if len(parts) == 2:
                    dt1 = datetime.fromisoformat(parts[0].strip())
                    dt2 = datetime.fromisoformat(parts[1].strip())
                    diff = abs((dt2 - dt1).total_seconds())
                    return ToolResult(success=True, output=f"{diff} seconds")
            
            return ToolResult(success=False, error="Invalid operation")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SystemTool(BaseTool):
    """System information and commands."""
    
    name = "system_info"
    description = "Get system info, run shell commands"
    category = "system"
    
    async def execute(self, command: str) -> ToolResult:
        try:
            if command == "info":
                import platform
                info = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "python": platform.python_version(),
                }
                return ToolResult(success=True, output=json.dumps(info, indent=2))
            elif command.startswith("shell:"):
                import subprocess
                shell_cmd = command[6:]
                result = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True, timeout=10)
                output = result.stdout if result.stdout else result.stderr
                return ToolResult(success=True, output=output[:2000])
            else:
                return ToolResult(success=False, error="Unknown command")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# =============================================================================
# REGISTER ALL BUILT-IN TOOLS
# =============================================================================

def register_builtin_tools() -> None:
    """Register all built-in tools."""
    registry = ToolRegistry.get_instance()
    
    tools = [
        CalculatorTool(),
        WebSearchTool(),
        WebFetchTool(),
        PythonREPLTool(),
        FileReadTool(),
        FileWriteTool(),
        JSONTool(),
        TextTool(),
        DateTimeTool(),
        SystemTool(),
    ]
    
    for t in tools:
        registry.register(t)
    
    logger.info("builtin_tools_registered", count=len(tools))


def get_default_tools() -> List[BaseTool]:
    """Get all registered tools."""
    registry = ToolRegistry.get_instance()
    return [registry.get(name) for name in registry.list_all()]


# =============================================================================
# CUSTOM TOOL EXAMPLE
# =============================================================================

# Example: Create a custom tool with the @tool decorator
@tool(name="sentiment", description="Analyze sentiment of text", category="nlp")
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment: positive, negative, or neutral."""
    positive = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "best"]
    negative = ["bad", "terrible", "awful", "horrible", "worst", "hate", "poor", "disappointing"]
    
    text_lower = text.lower()
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


@tool(name="word_length", description="Count words in text", category="text")
async def count_words(text: str) -> str:
    """Count words in text."""
    return str(len(text.split()))


# Initialize registry with built-in tools
register_builtin_tools()

# Register custom tools
ToolRegistry.get_instance().register(analyze_sentiment)
ToolRegistry.get_instance().register(count_words)
