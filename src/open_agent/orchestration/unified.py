"""Unified Orchestration Layer - All tools working together.

This is the main entry point that orchestrates:
- DeepAgent: Core AI agent
- OpenClaw: Multi-agent with SOUL.md
- OpenShell: Sandbox execution
- All Tools: Browser, Calculator, Code, etc.
"""

from __future__ import annotations

import asyncio
import os
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# UNIFIED ORCHESTRATOR
# =============================================================================

@dataclass
class OrchestratorConfig:
    """Configuration for the unified orchestrator."""
    llm_provider: str = "nvidia"
    llm_model: str = "nvidia/nemotron-3-super-120b-a12b"
    enable_sandbox: bool = True
    enable_browser: bool = True
    enable_tools: bool = True
    verbose: bool = True


class UnifiedOrchestrator:
    """The main orchestrator that combines all systems.
    
    Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │              UnifiedOrchestrator                         │
    ├─────────────────────────────────────────────────────────┤
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
    │  │ DeepAgent │  │ OpenClaw │  │ OpenShell│            │
    │  │  (Core)  │  │  (Crew)  │  │(Sandbox) │            │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
    │       │              │              │                    │
    │       └──────────────┼──────────────┘                    │
    │                      │                                    │
    │              ┌───────┴───────┐                          │
    │              │  ToolRegistry  │                          │
    │              │ Browser|Tools  │                          │
    │              └───────────────┘                           │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self._llm = None
        self._tools = {}
        self._agents = {}
        self._sandbox = None
        self._browser = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return
        
        logger.info("initializing_orchestrator")
        
        # Initialize LLM
        self._llm = self._create_llm()
        
        # Initialize tools
        self._initialize_tools()
        
        # Initialize sandbox
        if self.config.enable_sandbox:
            self._initialize_sandbox()
        
        # Initialize browser
        if self.config.enable_browser:
            self._initialize_browser()
        
        self._initialized = True
        logger.info("orchestrator_initialized")
    
    def _create_llm(self):
        """Create LLM instance."""
        from open_agent import LLMFactory, LLMProvider
        
        api_key = os.environ.get('NVIDIA_API_KEY') or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.warning("no_api_key_found")
            return None
        
        return LLMFactory.create(
            LLMProvider(self.config.llm_provider),
            api_key=api_key,
            model=self.config.llm_model
        )
    
    def _initialize_tools(self):
        """Initialize all tools."""
        from open_agent.tools.modular import ToolRegistry, register_builtin_tools
        
        register_builtin_tools()
        registry = ToolRegistry.get_instance()
        
        for name in registry.list_all():
            self._tools[name] = registry.get(name)
        
        logger.info("tools_initialized", count=len(self._tools))
    
    def _initialize_sandbox(self):
        """Initialize OpenShell sandbox."""
        try:
            from open_agent.integrations.openclawsdk import OpenShellBackend
            self._sandbox = OpenShellBackend()
            logger.info("sandbox_initialized")
        except Exception as e:
            logger.warning("sandbox_init_failed", error=str(e))
    
    def _initialize_browser(self):
        """Initialize browser automation."""
        try:
            from open_agent.automation.browser import BrowserTool
            self._browser = BrowserTool()
            logger.info("browser_initialized")
        except Exception as e:
            logger.warning("browser_init_failed", error=str(e))
    
    async def execute_tool(self, tool_name: str, *args, **kwargs) -> str:
        """Execute a tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found"
        
        try:
            result = await tool.execute(*args, **kwargs)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def execute_sandbox(self, command: str) -> Dict[str, Any]:
        """Execute in sandbox."""
        if not self._sandbox:
            return {"error": "Sandbox not initialized"}
        
        session = self._sandbox.create_sandbox()
        result = session.exec(command)
        session.terminate()
        return result
    
    async def browse(self, command: str) -> str:
        """Execute browser command."""
        if not self._browser:
            return "Browser not initialized"
        
        result = await self._browser.execute(command)
        return str(result)
    
    async def agent_task(self, agent_name: str, task: str) -> str:
        """Run task with an agent."""
        from open_agent import Agent, AgentConfig
        from open_agent.integrations.openclawsdk import SoulConfig
        
        soul = SoulConfig(name=agent_name, responsibilities=[task])
        agent = Agent(AgentConfig(
            name=agent_name,
            role=agent_name,
            goal=task,
            backstory=f"You are {agent_name}.",
            verbose=self.config.verbose,
            llm=self._llm,
            tools=list(self._tools.values()),
        ))
        
        return await agent.execute(task)
    
    async def crew_task(self, task: str, agents: List[str] = None) -> Dict[str, str]:
        """Run task with a crew of agents."""
        from open_agent import Crew, Task, Agent, AgentConfig
        from open_agent.integrations.openclawsdk import SoulConfig
        
        agents = agents or ["Researcher", "Writer"]
        agent_objs = []
        
        for name in agents:
            soul = SoulConfig(name=name, responsibilities=[task])
            agent_objs.append(Agent(AgentConfig(
                name=name.lower(),
                role=name,
                goal=task,
                backstory=f"You are {name}.",
                verbose=False,
                llm=self._llm,
                tools=list(self._tools.values())[:5],
            )))
        
        tasks = [
            Task(description=f"{task} - Agent: {name}", agent=agent)
            for name, agent in zip(agents, agent_objs)
        ]
        
        crew = Crew(
            agents=agent_objs,
            tasks=tasks,
            process=Crew.Process.SEQUENTIAL if len(agents) > 1 else Crew.Process.PARALLEL,
            verbose=self.config.verbose,
        )
        
        return await crew.kickoff()
    
    async def run(self, prompt: str) -> str:
        """Main entry point - intelligently route the prompt."""
        await self.initialize()
        
        prompt_lower = prompt.lower()
        
        # Check for tool commands
        if "browse:" in prompt_lower or "navigate:" in prompt_lower or "scrape:" in prompt_lower:
            cmd = prompt.split(":", 1)[1] if ":" in prompt else prompt
            return await self.browse(prompt)
        
        # Check for sandbox commands
        if prompt_lower.startswith("sandbox:") or prompt_lower.startswith("exec:"):
            cmd = prompt.split(":", 1)[1] if ":" in prompt else prompt
            result = await self.execute_sandbox(cmd)
            return result.get("stdout", str(result))
        
        # Check for tool execution
        tool_prefixes = ["calculate:", "search:", "python:", "code:"]
        for prefix in tool_prefixes:
            if prompt_lower.startswith(prefix):
                tool_name = prefix.replace(":", "")
                if tool_name == "calculate":
                    tool_name = "calculator"
                elif tool_name == "search":
                    tool_name = "web_search"
                elif tool_name in ["python", "code"]:
                    tool_name = "python_repl"
                
                arg = prompt.split(":", 1)[1] if ":" in prompt else prompt
                return await self.execute_tool(tool_name, arg)
        
        # Use LLM for everything else
        if self._llm:
            response = await self._llm.ainvoke([{"role": "user", "content": prompt}])
            return response
        
        return "No LLM configured"
    
    def list_tools(self) -> List[str]:
        """List all available tools."""
        return list(self._tools.keys())
    
    def status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "initialized": self._initialized,
            "llm": self._llm is not None,
            "tools": len(self._tools),
            "sandbox": self._sandbox is not None,
            "browser": self._browser is not None,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def orchestrate(prompt: str) -> str:
    """Run a prompt through the unified orchestrator."""
    orchestrator = UnifiedOrchestrator()
    return await orchestrator.run(prompt)


def create_orchestrator(
    llm_provider: str = "nvidia",
    enable_sandbox: bool = True,
    enable_browser: bool = True,
) -> UnifiedOrchestrator:
    """Create a configured orchestrator."""
    config = OrchestratorConfig(
        llm_provider=llm_provider,
        enable_sandbox=enable_sandbox,
        enable_browser=enable_browser,
    )
    return UnifiedOrchestrator(config)
