"""SmithAI - Unified AI Agent Framework

One framework to rule them all:
- DeepAgent: Core AI agent
- OpenClaw: Multi-agent orchestration
- OpenShell: Sandbox execution
- All Tools: Browser, Calculator, Code, etc.
"""

from __future__ import annotations

__version__ = "1.5.0"
__author__ = "Himan D <himanshu@open.ai>"
__status__ = "production"

# Core framework
from open_agent.framework import (
    Config, get_config,
    BaseLLM, LLMProvider, LLMFactory,
    Agent, AgentConfig, Task, Crew,
    create_agent, create_crew,
    BaseTool, ToolResult, ToolRegistry,
    get_default_tools,
    CalculatorTool, WebSearchTool, WebFetchTool,
    PythonREPLTool, FileReadTool, FileWriteTool,
)

# Orchestration
from open_agent.orchestration.unified import (
    UnifiedOrchestrator, OrchestratorConfig,
    orchestrate, create_orchestrator,
)

# Integrations
from open_agent.integrations.openclawsdk import (
    OpenShellBackend, SandboxSession, SandboxType,
    OpenClawAgent, OpenClawCrew, SoulConfig, Skill,
    create_openshell_sandbox, create_openclaw_agent, create_openclaw_crew,
)

# Automation
from open_agent.automation.browser import (
    BrowserTool, WebScraperTool, FormFillerTool,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    "__status__",
    
    # Core
    "Config", "get_config",
    "BaseLLM", "LLMProvider", "LLMFactory",
    "Agent", "AgentConfig", "Task", "Crew",
    "create_agent", "create_crew",
    
    # Tools
    "BaseTool", "ToolResult", "ToolRegistry",
    "get_default_tools",
    "CalculatorTool", "WebSearchTool", "WebFetchTool",
    "PythonREPLTool", "FileReadTool", "FileWriteTool",
    
    # Orchestration
    "UnifiedOrchestrator", "OrchestratorConfig",
    "orchestrate", "create_orchestrator",
    
    # Integrations
    "OpenShellBackend", "SandboxSession", "SandboxType",
    "OpenClawAgent", "OpenClawCrew", "SoulConfig", "Skill",
    "create_openshell_sandbox", "create_openclaw_agent", "create_openclaw_crew",
    
    # Automation
    "BrowserTool", "WebScraperTool", "FormFillerTool",
]
