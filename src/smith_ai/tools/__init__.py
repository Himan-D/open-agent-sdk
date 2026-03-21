"""Tool System - Registry and decorator for custom tools.

Usage:
    from smith_ai.tools import tool, register_tool, get_tool
    
    @tool(name="calculator", description="Perform calculations")
    async def calculate(expression: str) -> str:
        return str(eval(expression))
    
    result = await get_tool("calculator").execute("2 + 2")
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field

from smith_ai.core.types import BaseTool, ToolResult, ToolSchema


class ToolRegistry:
    """Central singleton registry for all tools."""
    
    _instance: Optional[ToolRegistry] = None
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    @classmethod
    def get_instance(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance
    
    def register(self, tool: BaseTool, category: Optional[str] = None) -> None:
        self._tools[tool.name] = tool
        cat = category or tool.category
        if cat not in self._categories:
            self._categories[cat] = []
        if tool.name not in self._categories[cat]:
            self._categories[cat].append(tool.name)
    
    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            for cat in self._categories:
                if name in self._categories[cat]:
                    self._categories[cat].remove(name)
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    
    def list_all(self) -> List[str]:
        return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[BaseTool]:
        return [self._tools[n] for n in self._categories.get(category, []) if n in self._tools]
    
    def list_categories(self) -> List[str]:
        return list(self._categories.keys())


def register_tool(tool: BaseTool, category: Optional[str] = None) -> None:
    ToolRegistry.get_instance().register(tool, category)


def get_tool(name: str) -> Optional[BaseTool]:
    return ToolRegistry.get_instance().get(name)


def list_tools() -> List[str]:
    return ToolRegistry.get_instance().list_all()


def tool(name: str, description: str = "", category: str = "custom", **schema_kwargs):
    """Decorator to create a tool from an async function.
    
    Example:
        @tool(name="search", description="Search the web")
        async def search(query: str) -> str:
            return f"Results for: {query}"
    """
    def decorator(func: Callable) -> BaseTool:
        async def async_wrapper(*args, **kwargs) -> ToolResult:
            try:
                result = await func(*args, **kwargs)
                return ToolResult(tool_call_id="", success=True, output=str(result))
            except Exception as e:
                return ToolResult(tool_call_id="", success=False, error=str(e))
        
        def sync_wrapper(*args, **kwargs) -> ToolResult:
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return ToolResult(tool_call_id="", success=False, error="Use async function")
                return ToolResult(tool_call_id="", success=True, output=str(result))
            except Exception as e:
                return ToolResult(tool_call_id="", success=False, error=str(e))
        
        _name = name
        _desc = description or func.__doc__ or ""
        _cat = category
        
        class CustomTool(BaseTool):
            name = _name
            description = _desc
            category = _cat
            
            async def execute(self, *args, **kwargs) -> ToolResult:
                if asyncio.iscoroutinefunction(func):
                    return await async_wrapper(*args, **kwargs)
                return sync_wrapper(*args, **kwargs)
        
        return CustomTool()
    return decorator


def create_tool_from_function(func: Callable, name: str, description: str = "", category: str = "custom") -> BaseTool:
    """Create a tool from a regular function."""
    return tool(name=name, description=description, category=category)(func)


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate mathematical expressions"
    category = "math"
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return ToolResult(tool_call_id="", success=True, output=str(result))
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information"
    category = "research"
    
    async def execute(self, query: str) -> ToolResult:
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return ToolResult(tool_call_id="", success=False, error="ddgs not installed (pip install ddgs)")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            output = "\n".join([f"- {r['title']}: {r['href']}" for r in results])
            return ToolResult(tool_call_id="", success=True, output=output or "No results found")
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class WebFetchTool(BaseTool):
    name = "fetch_url"
    description = "Fetch content from a URL"
    category = "web"
    
    async def execute(self, url: str) -> ToolResult:
        try:
            import httpx
            response = await httpx.AsyncClient().get(url, timeout=10)
            return ToolResult(tool_call_id="", success=True, output=response.text[:5000])
        except ImportError:
            return ToolResult(tool_call_id="", success=False, error="httpx not installed")
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class PythonREPLTool(BaseTool):
    name = "python_repl"
    description = "Execute Python code"
    category = "code"
    
    async def execute(self, code: str) -> ToolResult:
        try:
            import io
            from contextlib import redirect_stdout
            
            output = io.StringIO()
            with redirect_stdout(output):
                exec(code, {"__builtins__": __builtins__})
            
            result = output.getvalue()
            return ToolResult(tool_call_id="", success=True, output=result or "Code executed successfully")
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class FileReadTool(BaseTool):
    name = "read_file"
    description = "Read contents of a file"
    category = "filesystem"
    
    async def execute(self, path: str) -> ToolResult:
        try:
            with open(path, "r") as f:
                content = f.read()
            return ToolResult(tool_call_id="", success=True, output=content[:10000])
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class FileWriteTool(BaseTool):
    name = "write_file"
    description = "Write content to a file"
    category = "filesystem"
    
    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            with open(path, "w") as f:
                f.write(content)
            return ToolResult(tool_call_id="", success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class JSONTool(BaseTool):
    name = "json_tool"
    description = "Parse and validate JSON"
    category = "utility"
    
    async def execute(self, data: str, operation: str = "parse") -> ToolResult:
        try:
            if operation == "parse":
                parsed = json.loads(data)
                return ToolResult(tool_call_id="", success=True, output=json.dumps(parsed, indent=2))
            elif operation == "validate":
                json.loads(data)
                return ToolResult(tool_call_id="", success=True, output="Valid JSON")
            else:
                return ToolResult(tool_call_id="", success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


class DateTimeTool(BaseTool):
    name = "datetime_tool"
    description = "Get current date and time"
    category = "utility"
    
    async def execute(self, format: str = "%Y-%m-%d %H:%M:%S") -> ToolResult:
        from datetime import datetime
        now = datetime.now()
        return ToolResult(tool_call_id="", success=True, output=now.strftime(format))


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Get system information"
    category = "system"
    
    async def execute(self) -> ToolResult:
        import platform
        import sys
        
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
        }
        return ToolResult(tool_call_id="", success=True, output=json.dumps(info, indent=2))


class SentimentTool(BaseTool):
    name = "sentiment"
    description = "Analyze sentiment of text"
    category = "nlp"
    
    async def execute(self, text: str) -> ToolResult:
        positive = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "best", "awesome"]
        negative = ["bad", "terrible", "awful", "horrible", "worst", "hate", "poor", "disappointing"]
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive if w in text_lower)
        neg_count = sum(1 for w in negative if w in text_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return ToolResult(tool_call_id="", success=True, output=f"Sentiment: {sentiment} (positive: {pos_count}, negative: {neg_count})")


class TextTool(BaseTool):
    name = "text_tool"
    description = "Text manipulation utilities"
    category = "utility"
    
    async def execute(self, text: str, operation: str) -> ToolResult:
        try:
            ops = {
                "upper": text.upper,
                "lower": text.lower,
                "reverse": lambda: text[::-1],
                "word_count": lambda: str(len(text.split())),
                "char_count": lambda: str(len(text)),
                "strip": text.strip,
            }
            
            if operation not in ops:
                return ToolResult(tool_call_id="", success=False, error=f"Unknown operation: {operation}")
            
            result = ops[operation]() if callable(ops[operation]) else ops[operation]
            return ToolResult(tool_call_id="", success=True, output=str(result))
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


def register_builtin_tools() -> None:
    """Register all built-in tools."""
    registry = ToolRegistry.get_instance()
    
    builtin_tools = [
        CalculatorTool(),
        WebSearchTool(),
        WebFetchTool(),
        PythonREPLTool(),
        FileReadTool(),
        FileWriteTool(),
        JSONTool(),
        DateTimeTool(),
        SystemInfoTool(),
        SentimentTool(),
        TextTool(),
    ]
    
    for tool in builtin_tools:
        registry.register(tool)


from smith_ai.core.types import BaseTool, ToolResult

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "ToolSchema",
    "tool",
    "create_tool_from_function",
    "register_tool",
    "get_tool",
    "list_tools",
    "register_builtin_tools",
    "CalculatorTool",
    "WebSearchTool",
    "WebFetchTool",
    "PythonREPLTool",
    "FileReadTool",
    "FileWriteTool",
    "JSONTool",
    "DateTimeTool",
    "SystemInfoTool",
    "SentimentTool",
    "TextTool",
]
