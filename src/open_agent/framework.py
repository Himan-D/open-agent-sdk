"""SmithAI - Production AI Agent Framework

Unified multi-LLM agent orchestration with Crew-style workflows.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Himan D <himanshu@open.ai>"

import os
import asyncio
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

# Import tools from modular system
try:
    from open_agent.tools.modular import (
        BaseTool as ToolBase,
        ToolResult as ToolResult,
        ToolRegistry,
        get_default_tools as _get_default_tools,
        create_tool,
        tool,
    )
except ImportError:
    # Fallback if tools not available
    class ToolBase:
        name = "base"
        description = "base"
    
    class ToolResult:
        def __init__(self, success, output="", error=""):
            self.success = success
            self.output = output
            self.error = error
    
    def _get_default_tools():
        return []
    
    def create_tool(*args, **kwargs):
        raise NotImplementedError("Tools module not available")
    
    def tool(*args, **kwargs):
        def decorator(f): return f
        return decorator


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class Config:
    """Global configuration."""
    nvidia_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    default_provider: str = "nvidia"
    default_model: str = "nvidia/nemotron-3-super-120b-a12b"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    memory_path: str = "./memory"
    verbose: bool = True
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment."""
        return cls(
            nvidia_api_key=os.getenv("NVIDIA_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            default_provider=os.getenv("DEFAULT_LLM_PROVIDER", "nvidia"),
            default_model=os.getenv("DEFAULT_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
            verbose=os.getenv("VERBOSE", "true").lower() == "true",
        )


_config: Optional[Config] = None

def get_config() -> Config:
    """Get global config."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


# =============================================================================
# LLM PROVIDER SYSTEM
# =============================================================================

class LLMProvider(Enum):
    """Supported LLM providers."""
    NVIDIA = "nvidia"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE = "azure"
    MISTRAL = "mistral"
    COHERE = "cohere"


class BaseLLM(ABC):
    """Base class for all LLM providers."""
    
    @abstractmethod
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Async invoke - main interface."""
        pass
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Async invoke alias."""
        pass
    
    def invoke_sync(self, messages: List[Dict[str, str]]) -> str:
        """Sync invoke wrapper."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.ainvoke(messages))
                    return future.result()
            return loop.run_until_complete(self.ainvoke(messages))
        except RuntimeError:
            return asyncio.run(self.ainvoke(messages))


class NVIDIAProvider(BaseLLM):
    """NVIDIA NIM/MiMa via LangChain."""
    
    def __init__(self, api_key: str, model: str = "nvidia/nemotron-3-super-120b-a12b", 
                 base_url: str = "https://integrate.api.nvidia.com/v1",
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
            self._client = ChatNVIDIA(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
        
        response = await self._get_client().ainvoke(lc_messages)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        return await self.invoke(messages)
    
    def stream(self, messages: List[Dict[str, str]]):
        from langchain_core.messages import HumanMessage, SystemMessage
        
        lc_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                lc_messages.append(SystemMessage(content=msg.get("content", "")))
            else:
                lc_messages.append(HumanMessage(content=msg.get("content", "")))
        
        return self._get_client().stream(lc_messages)


class OpenAIProvider(BaseLLM):
    """OpenAI GPT models."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", 
                 base_url: Optional[str] = None, temperature: float = 0.7, 
                 max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        return await self.invoke(messages)


class AnthropicProvider(BaseLLM):
    """Anthropic Claude models."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022",
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        system = ""
        chat_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                chat_messages.append({"role": msg.get("role", "user"), 
                                      "content": msg.get("content", "")})
        
        response = await client.messages.create(
            model=self.model,
            system=system,
            messages=chat_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.content[0].text
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        return await self.invoke(messages)


class GoogleProvider(BaseLLM):
    """Google Gemini models."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp",
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from google import genai
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._client
        
        contents = []
        for msg in messages:
            if msg.get("role") != "system":
                contents.append({
                    "role": "user" if msg.get("role") == "user" else "model",
                    "parts": [msg.get("content", "")]
                })
        
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=contents,
        )
        return response.text
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        return await self.invoke(messages)


class OllamaProvider(BaseLLM):
    """Ollama local models."""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434",
                 temperature: float = 0.7, max_tokens: int = 4096):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(base_url=f"{self.base_url}/v1", api_key="ollama")
        return self._client
    
    async def invoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        return await self.invoke(messages)


class LLMFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        LLMProvider.NVIDIA: NVIDIAProvider,
        LLMProvider.OPENAI: OpenAIProvider,
        LLMProvider.ANTHROPIC: AnthropicProvider,
        LLMProvider.GOOGLE: GoogleProvider,
        LLMProvider.OLLAMA: OllamaProvider,
    }
    
    @classmethod
    def create(cls, provider: Union[str, LLMProvider], **kwargs) -> BaseLLM:
        """Create an LLM provider instance."""
        if isinstance(provider, str):
            provider = LLMProvider(provider)
        
        provider_class = cls._providers.get(provider)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider}")
        
        return provider_class(**kwargs)
    
    @classmethod
    def create_from_config(cls, config: Config = None) -> BaseLLM:
        """Create from global config."""
        config = config or get_config()
        
        provider = LLMProvider(config.default_provider)
        
        kwargs = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        
        if provider == LLMProvider.NVIDIA:
            kwargs["api_key"] = config.nvidia_api_key
            kwargs["model"] = config.default_model
        elif provider == LLMProvider.OPENAI:
            kwargs["api_key"] = config.openai_api_key
            kwargs["model"] = "gpt-4o"
        elif provider == LLMProvider.ANTHROPIC:
            kwargs["api_key"] = config.anthropic_api_key
            kwargs["model"] = "claude-3-5-sonnet-20241022"
        elif provider == LLMProvider.GOOGLE:
            kwargs["api_key"] = config.google_api_key
            kwargs["model"] = "gemini-2.0-flash-exp"
        elif provider == LLMProvider.OLLAMA:
            kwargs["model"] = "llama3.2"
        
        return cls.create(provider, **kwargs)


# =============================================================================
# TOOL SYSTEM
# =============================================================================

class ToolResult:
    """Result from tool execution."""
    
    def __init__(self, success: bool, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"


class BaseTool(ABC):
    """Base class for all tools."""
    
    name: str = "base_tool"
    description: str = "A base tool"
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
    
    def __call__(self, *args, **kwargs) -> ToolResult:
        return asyncio.run(self.execute(*args, **kwargs))


class CalculatorTool(BaseTool):
    """Mathematical calculator tool."""
    
    name = "calculator"
    description = "Perform mathematical calculations. Input: mathematical expression"
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            import math
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": math.sqrt,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "log": math.log, "pi": math.pi, "e": math.e,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebSearchTool(BaseTool):
    """Web search tool."""
    
    name = "web_search"
    description = "Search the web. Input: search query"
    
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
            
            return ToolResult(success=True, output="\n".join(results) or "No results found")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WikipediaTool(BaseTool):
    """Wikipedia search tool."""
    
    name = "wikipedia"
    description = "Search Wikipedia. Input: topic"
    
    async def execute(self, topic: str) -> ToolResult:
        try:
            import wikipedia
            summary = wikipedia.summary(topic, sentences=3)
            return ToolResult(success=True, output=summary)
        except ImportError:
            return ToolResult(success=False, error="wikipedia package not installed")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class PythonREPLTool(BaseTool):
    """Python code execution tool."""
    
    name = "python_repl"
    description = "Execute Python code. Input: Python code to execute"
    
    async def execute(self, code: str) -> ToolResult:
        try:
            import io, contextlib, traceback
            
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    exec(code, {"__builtins__": __builtins__})
                result = output.getvalue() or "Executed successfully (no output)"
            except Exception:
                output.write(traceback.format_exc())
                result = output.getvalue()
            
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileReadTool(BaseTool):
    """Read files."""
    
    name = "read_file"
    description = "Read a file. Input: file path"
    
    async def execute(self, path: str) -> ToolResult:
        try:
            with open(path, 'r') as f:
                content = f.read()
            return ToolResult(success=True, output=content)
        except FileNotFoundError:
            return ToolResult(success=False, error=f"File not found: {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileWriteTool(BaseTool):
    """Write files."""
    
    name = "write_file"
    description = "Write to a file. Input: path|content (separated by |)"
    
    async def execute(self, path: str, content: str = "") -> ToolResult:
        try:
            if "|" in path and not content:
                parts = path.split("|", 1)
                path, content = parts[0], parts[1]
            
            with open(path.strip(), 'w') as f:
                f.write(content)
            return ToolResult(success=True, output=f"Written to {path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebFetchTool(BaseTool):
    """Fetch URL content."""
    
    name = "fetch_url"
    description = "Fetch content from URL. Input: URL"
    
    async def execute(self, url: str) -> ToolResult:
        try:
            import httpx
            response = httpx.get(url, timeout=10)
            content = response.text[:5000]
            if len(response.text) > 5000:
                content += "\n... (truncated)"
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ToolRegistry:
    """Registry for available tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self._tools.keys())
    
    async def execute(self, name: str, *args, **kwargs) -> ToolResult:
        """Execute a tool."""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        return await tool.execute(*args, **kwargs)


def get_default_tools() -> List[BaseTool]:
    """Get default tools from the modular system."""
    return _get_default_tools()


# =============================================================================
# MEMORY SYSTEM
# =============================================================================

class MemoryStore:
    """Persistent memory storage."""
    
    def __init__(self, path: str = "./memory"):
        self.path = path
        import os
        os.makedirs(path, exist_ok=True)
        self._memory_file = os.path.join(path, "MEMORY.md")
        self._init_memory_file()
    
    def _init_memory_file(self):
        """Initialize memory file if it doesn't exist."""
        import os
        if not os.path.exists(self._memory_file):
            with open(self._memory_file, 'w') as f:
                f.write("# Agent Memory\n\n")
                f.write("## Session History\n\n")
                f.write("## Important Facts\n\n")
                f.write("## Preferences\n\n")
    
    async def add(self, content: str, category: str = "general"):
        """Add to memory."""
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        
        with open(self._memory_file, 'a') as f:
            f.write(f"\n### [{timestamp}] {category}\n")
            f.write(f"{content}\n")
    
    async def search(self, query: str) -> str:
        """Search memory."""
        import os
        if not os.path.exists(self._memory_file):
            return "No memory found."
        
        with open(self._memory_file, 'r') as f:
            content = f.read()
        
        if query.lower() in content.lower():
            return f"Found references to '{query}' in memory"
        return "No relevant memories found."
    
    async def get_all(self) -> str:
        """Get all memory."""
        import os
        if not os.path.exists(self._memory_file):
            return ""
        
        with open(self._memory_file, 'r') as f:
            return f.read()


# =============================================================================
# AGENT SYSTEM
# =============================================================================

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    tools: List[BaseTool] = field(default_factory=list)
    llm: Optional[BaseLLM] = None
    memory: Optional[MemoryStore] = None


class Agent:
    """Autonomous agent that can execute tasks.
    
    Example:
        >>> agent = Agent(
        ...     name="researcher",
        ...     role="Researcher",
        ...     goal="Find and summarize information",
        ...     backstory="You are a professional researcher"
        ... )
        >>> result = await agent.execute("Research AI trends in 2025")
    """
    
    def __init__(self, config: Union[AgentConfig, Dict[str, Any]]):
        if isinstance(config, dict):
            config = AgentConfig(**config)
        
        self.config = config
        self.name = config.name
        self.role = config.role
        self.goal = config.goal
        self.backstory = config.backstory
        self.verbose = config.verbose
        self.tools = config.tools
        self.llm = config.llm
        self.memory = config.memory
        
        self._tool_registry = ToolRegistry()
        for tool in self.tools:
            self._tool_registry.register(tool)
        
        self._conversation_history: List[Dict[str, str]] = []
    
    def _build_system_prompt(self) -> str:
        """Build the agent's system prompt."""
        tools_desc = ""
        if self.tools:
            tools_desc = "\n\n## Available Tools\n"
            for tool in self.tools:
                tools_desc += f"- {tool.name}: {tool.description}\n"
        
        return f"""You are {self.role}.

YOUR GOAL: {self.goal}

BACKSTORY: {self.backstory}

{tools_desc}

## Guidelines:
- Think step by step when solving complex problems
- Use tools when appropriate
- Provide clear, actionable responses
- If you need to use a tool, respond with: TOOL:tool_name:args"""
    
    async def think(self, prompt: str) -> str:
        """Process a prompt through the LLM."""
        if not self.llm:
            self.llm = LLMFactory.create_from_config()
        
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *self._conversation_history,
            {"role": "user", "content": prompt},
        ]
        
        response = await self.llm.ainvoke(messages)
        
        self._conversation_history.append({"role": "user", "content": prompt})
        self._conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    async def execute(self, task: str) -> str:
        """Execute a task, handling tool calls."""
        if self.verbose:
            logger.info(f"[{self.name}] Executing: {task[:50]}...")
        
        response = await self.think(task)
        
        while response.startswith("TOOL:") and ":" in response:
            parts = response.split(":", 2)
            tool_name = parts[1]
            tool_args = parts[2] if len(parts) > 2 else ""
            
            tool_result = await self._tool_registry.execute(tool_name, tool_args)
            
            if self.verbose:
                logger.info(f"[{self.name}] Tool {tool_name} result: {str(tool_result)[:50]}...")
            
            response = await self.think(f"Tool result: {tool_result}\n\nContinue with the task.")
        
        if self.memory:
            await self.memory.add(f"{self.name} completed: {task}", category="task")
        
        return response
    
    async def reset(self):
        """Reset agent state."""
        self._conversation_history = []


# =============================================================================
# CREW SYSTEM (Multi-Agent Orchestration)
# =============================================================================

@dataclass
class Task:
    """A task to be executed by an agent.
    
    Example:
        >>> task = Task(
        ...     description="Research AI trends",
        ...     agent=researcher,
        ...     expected_output="Summary of 5 key AI trends"
        ... )
    """
    description: str
    agent: Optional[Agent] = None
    expected_output: Optional[str] = None
    context: Optional[List["Task"]] = None
    async_execution: bool = False
    
    _result: Optional[str] = None
    _status: str = "pending"
    
    @property
    def result(self) -> Optional[str]:
        return self._result
    
    @property
    def status(self) -> str:
        return self._status


class Crew:
    """Multi-agent crew orchestration.
    
    Example:
        >>> crew = Crew(
        ...     agents=[researcher, writer, coder],
        ...     tasks=[research_task, write_task, code_task],
        ...     process=Process.SEQUENTIAL,
        ...     verbose=True
        ... )
        >>> results = await crew.kickoff()
    """
    
    class Process(Enum):
        SEQUENTIAL = "sequential"
        PARALLEL = "parallel"
        HIERARCHICAL = "hierarchical"
    
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.SEQUENTIAL,
        verbose: bool = True,
        memory: Optional[MemoryStore] = None,
    ):
        self.agents = {a.name: a for a in agents}
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.memory = memory or MemoryStore()
        
        for task in tasks:
            if task.agent and task.agent.name not in self.agents:
                self.agents[task.agent.name] = task.agent
    
    async def _execute_task(self, task: Task) -> str:
        """Execute a single task."""
        if not task.agent:
            raise ValueError(f"Task '{task.description}' has no assigned agent")
        
        task._status = "in_progress"
        
        context = ""
        if task.context:
            context = "\n\n## Context from previous tasks:\n"
            for ctx_task in task.context:
                if ctx_task.result:
                    context += f"- {ctx_task.description}: {ctx_task.result}\n"
        
        prompt = f"""## Task: {task.description}
{context}
## Expected Output: {task.expected_output or 'A comprehensive response'}

Execute this task and provide your output."""
        
        try:
            result = await task.agent.execute(prompt)
            task._result = result
            task._status = "completed"
            
            if self.verbose:
                logger.info(f"[{task.agent.name}] Completed: {task.description[:50]}...")
            
            return result
        except Exception as e:
            task._status = "failed"
            task._result = str(e)
            logger.error(f"Task failed: {task.description}", error=str(e))
            return str(e)
    
    async def kickoff(self) -> Dict[str, Any]:
        """Execute all tasks and return results."""
        if self.verbose:
            logger.info(f"Crew starting with {len(self.tasks)} tasks")
        
        if self.process == self.Process.SEQUENTIAL:
            return await self._sequential()
        elif self.process == self.Process.PARALLEL:
            return await self._parallel()
        elif self.process == self.Process.HIERARCHICAL:
            return await self._hierarchical()
        else:
            raise ValueError(f"Unknown process: {self.process}")
    
    async def _sequential(self) -> Dict[str, str]:
        """Execute tasks sequentially with context passing."""
        results = {}
        for i, task in enumerate(self.tasks):
            task.context = self.tasks[:i] if i > 0 else None
            result = await self._execute_task(task)
            results[task.description] = result
        return results
    
    async def _parallel(self) -> Dict[str, str]:
        """Execute independent tasks in parallel."""
        async def run(task: Task):
            return task.description, await self._execute_task(task)
        
        results = await asyncio.gather(*[run(t) for t in self.tasks])
        return dict(results)
    
    async def _hierarchical(self) -> Dict[str, str]:
        """Execute with manager agent (first agent is manager)."""
        if not self.agents:
            raise ValueError("No agents in crew")
        
        manager = list(self.agents.values())[0]
        
        assignment_prompt = f"""As the {manager.role}, analyze these tasks and ensure proper coordination:

Tasks:
{chr(10).join(f"- {t.description} (assigned to: {t.agent.role if t.agent else 'unassigned'})" for t in self.tasks)}

Coordinate the execution and ensure all tasks are completed successfully."""
        
        await manager.execute(assignment_prompt)
        
        results = {}
        for task in self.tasks:
            result = await self._execute_task(task)
            results[task.description] = result
        
        return results
    
    def kickoff_sync(self) -> Dict[str, Any]:
        """Synchronous kickoff wrapper."""
        return asyncio.run(self.kickoff())


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def create_agent(
    name: str,
    role: str,
    goal: str,
    backstory: str,
    provider: str = "nvidia",
    tools: Optional[List[BaseTool]] = None,
    verbose: bool = True,
) -> Agent:
    """Create a configured agent."""
    config = get_config()
    
    llm_kwargs = {"temperature": config.temperature, "max_tokens": config.max_tokens}
    
    if provider == "nvidia":
        llm_kwargs["api_key"] = config.nvidia_api_key
        llm_kwargs["model"] = config.default_model
    elif provider == "openai":
        llm_kwargs["api_key"] = config.openai_api_key
    elif provider == "anthropic":
        llm_kwargs["api_key"] = config.anthropic_api_key
    elif provider == "ollama":
        llm_kwargs["model"] = "llama3.2"
    
    llm = LLMFactory.create(provider, **llm_kwargs)
    
    return Agent(AgentConfig(
        name=name,
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=verbose,
        tools=tools or get_default_tools(),
        llm=llm,
        memory=MemoryStore(config.memory_path),
    ))


def create_crew(
    agents_config: List[Dict[str, Any]],
    tasks_config: List[Dict[str, Any]],
    process: str = "sequential",
    verbose: bool = True,
) -> Crew:
    """Create a configured crew from config dicts.
    
    Example:
        >>> crew = create_crew(
        ...     agents_config=[{"name": "r", "role": "R", "goal": "G", "backstory": "B"}],
        ...     tasks_config=[{"description": "Do X", "agent": "r"}],
        ... )
        >>> results = await crew.kickoff()
    """
    agents = []
    for cfg in agents_config:
        cfg_copy = cfg.copy()
        provider = cfg_copy.pop("provider", "nvidia")
        
        llm_kwargs = {"temperature": 0.7, "max_tokens": 4096}
        config = get_config()
        
        if provider == "nvidia":
            llm_kwargs["api_key"] = config.nvidia_api_key
            llm_kwargs["model"] = config.default_model
        elif provider == "openai":
            llm_kwargs["api_key"] = config.openai_api_key
        elif provider == "anthropic":
            llm_kwargs["api_key"] = config.anthropic_api_key
        elif provider == "ollama":
            llm_kwargs["model"] = "llama3.2"
        
        llm = LLMFactory.create(provider, **llm_kwargs)
        
        agent = Agent(AgentConfig(
            name=cfg_copy["name"],
            role=cfg_copy["role"],
            goal=cfg_copy["goal"],
            backstory=cfg_copy["backstory"],
            verbose=verbose,
            tools=get_default_tools(),
            llm=llm,
        ))
        agents.append(agent)
    
    tasks = []
    for cfg in tasks_config:
        cfg_copy = cfg.copy()
        agent_name = cfg_copy.pop("agent", None)
        if agent_name:
            cfg_copy["agent"] = next((a for a in agents if a.name == agent_name), None)
        tasks.append(Task(**cfg_copy))
    
    return Crew(
        agents=agents,
        tasks=tasks,
        process=Crew.Process(process),
        verbose=verbose,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Example usage."""
    print("SmithAI - Production AI Agent Framework")
    print("=" * 50)
    
    agent = await create_agent(
        name="assistant",
        role="AI Assistant",
        goal="Help users with their questions",
        backstory="You are a helpful AI assistant powered by NVIDIA Nemotron"
    )
    
    result = await agent.execute("What is 2+2? Calculate using the calculator tool.")
    print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
