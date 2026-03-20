"""SmithAI - Production AI Agent Framework

Unified multi-LLM agent orchestration with Crew-style workflows.
Built with NVIDIA Nemotron, OpenAI, Anthropic, and more.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Himan D <himanshu@open.ai>"
__status__ = "production"

from open_agent.framework import (
    Config,
    get_config,
    BaseLLM,
    LLMProvider,
    LLMFactory,
    Agent,
    AgentConfig,
    Task,
    Crew,
    create_crew,
)

from open_agent.tools.modular import (
    BaseTool,
    ToolResult,
    ToolRegistry,
    create_tool,
    tool,
    get_default_tools,
    CalculatorTool,
    WebSearchTool,
    WebFetchTool,
    PythonREPLTool,
    FileReadTool,
    FileWriteTool,
    JSONTool,
    TextTool,
    DateTimeTool,
    SystemTool,
)

__all__ = [
    "__version__",
    "__author__",
    "__status__",
    "Config",
    "get_config",
    "BaseLLM",
    "LLMProvider",
    "LLMFactory",
    "Agent",
    "AgentConfig",
    "Task",
    "Crew",
    "create_crew",
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "create_tool",
    "tool",
    "get_default_tools",
    "CalculatorTool",
    "WebSearchTool",
    "WebFetchTool",
    "PythonREPLTool",
    "FileReadTool",
    "FileWriteTool",
    "JSONTool",
    "TextTool",
    "DateTimeTool",
    "SystemTool",
]
