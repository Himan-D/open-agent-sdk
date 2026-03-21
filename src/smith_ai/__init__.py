"""SmithAI - Enterprise AI Agent Framework.

Browser automation, multi-agent orchestration, and integrations for the enterprise.
"""

__version__ = "2.0.0"
__author__ = "Himan D <himanshu@open.ai>"
__status__ = "production"

from smith_ai.core import (
    AgentMessage,
    ToolCall,
    ToolResult,
    ToolSchema,
    AgentConfig,
    ExecutionResult,
    BaseLLM,
    BaseTool,
    LLMProvider,
    Process,
)

from smith_ai.llm import (
    LLMConfig,
    LLMRegistry,
    create_llm,
)

from smith_ai.tools import (
    ToolRegistry,
    tool,
    register_tool,
    register_builtin_tools,
    get_tool,
    list_tools,
    CalculatorTool,
    WebSearchTool,
    PythonREPLTool,
    JSONTool,
)

from smith_ai.agents import (
    Agent,
    Task,
    Crew,
    create_agent,
    create_crew,
)

from smith_ai.runtime import (
    Runtime,
    RuntimeConfig,
)

from smith_ai.sandbox import (
    Sandbox,
    SandboxSession,
    SandboxTool,
)

from smith_ai.browser import (
    BrowserSession,
    BrowserTool,
    WebScraper,
)

from smith_ai.browser.stealth import (
    StealthBrowser,
    StealthConfig,
    DetectionLevel,
    HumanBehavior,
)

from smith_ai.browser.remote import (
    RemoteBrowser,
    BrowserPool,
    BrowserType,
)

from smith_ai.captcha import (
    CaptchaSolver,
    CaptchaDetector,
    CaptchaAutomation,
    CaptchaType,
)

from smith_ai.tui import (
    TUIBridge,
    create_tui_app,
)

from smith_ai.integrations import (
    GitHubClient,
    GitHubConfig,
    SlackClient,
    SlackWebhook,
    DiscordWebhook,
    DiscordBot,
    NotionClient,
    NotionConfig,
    JiraClient,
    JiraConfig,
    GoogleWorkspace,
    GoogleConfig,
)

from smith_ai.edge import (
    OllamaClient,
    OllamaConfig,
    LlamaCppServer,
    TransformersLocal,
    TGIClient,
    LocalModelFactory,
    EdgeDeploymentConfig,
    ModelSize,
    ModelInfo,
)

from smith_ai.memory import (
    Document,
    SearchResult,
    MemoryConfig,
    VectorStore,
    InMemoryVectorStore,
    ChromaStore,
    FAISSStore,
    PineconeStore,
    MemoryStore,
    KnowledgeGraph,
    EmbeddingModel,
    get_embeddings,
    cosine_similarity,
)

from smith_ai.enterprise import (
    RateLimitConfig,
    RateLimitStrategy,
    RateLimiter,
    RateLimitExceeded,
    TokenBucket,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    CircuitState,
    RetryConfig,
    retry,
    CacheBackend,
    MemoryCache,
    RedisCache,
    cached,
    SecretsManager,
    Observability,
    EnterpriseConfig,
    EnterpriseManager,
)

from smith_ai.storage import (
    DatabaseConfig,
    RedisConfig,
    MongoConfig,
    PostgresTool,
    MongoTool,
    RedisTool,
    S3Tool,
    GCSStorage,
)

__all__ = [
    "__version__",
    "__author__",
    "__status__",
    # Core
    "AgentMessage",
    "ToolCall",
    "ToolResult",
    "ToolSchema",
    "AgentConfig",
    "ExecutionResult",
    "BaseLLM",
    "BaseTool",
    "LLMProvider",
    "Process",
    "LLMConfig",
    "LLMRegistry",
    "create_llm",
    # Tools
    "ToolRegistry",
    "tool",
    "register_tool",
    "register_builtin_tools",
    "get_tool",
    "list_tools",
    "CalculatorTool",
    "WebSearchTool",
    "PythonREPLTool",
    "JSONTool",
    # Agents
    "Agent",
    "Task",
    "Crew",
    "create_agent",
    "create_crew",
    # Runtime
    "Runtime",
    "RuntimeConfig",
    # Sandbox
    "Sandbox",
    "SandboxSession",
    "SandboxTool",
    # Browser
    "BrowserSession",
    "BrowserTool",
    "WebScraper",
    "StealthBrowser",
    "StealthConfig",
    "DetectionLevel",
    "HumanBehavior",
    "RemoteBrowser",
    "BrowserPool",
    "BrowserType",
    # Captcha
    "CaptchaSolver",
    "CaptchaDetector",
    "CaptchaAutomation",
    "CaptchaType",
    # TUI
    "TUIBridge",
    "create_tui_app",
    # Integrations
    "GitHubClient",
    "GitHubConfig",
    "SlackClient",
    "SlackWebhook",
    "DiscordWebhook",
    "DiscordBot",
    "NotionClient",
    "NotionConfig",
    "JiraClient",
    "JiraConfig",
    "GoogleWorkspace",
    "GoogleConfig",
    # Edge AI
    "OllamaClient",
    "OllamaConfig",
    "LlamaCppServer",
    "TransformersLocal",
    "TGIClient",
    "LocalModelFactory",
    "EdgeDeploymentConfig",
    "ModelSize",
    "ModelInfo",
    # Memory
    "Document",
    "SearchResult",
    "MemoryConfig",
    "VectorStore",
    "InMemoryVectorStore",
    "ChromaStore",
    "FAISSStore",
    "PineconeStore",
    "MemoryStore",
    "KnowledgeGraph",
    "EmbeddingModel",
    "get_embeddings",
    "cosine_similarity",
    # Enterprise
    "RateLimitConfig",
    "RateLimitStrategy",
    "RateLimiter",
    "RateLimitExceeded",
    "TokenBucket",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpen",
    "CircuitState",
    "RetryConfig",
    "retry",
    "CacheBackend",
    "MemoryCache",
    "RedisCache",
    "cached",
    "SecretsManager",
    "Observability",
    "EnterpriseConfig",
    "EnterpriseManager",
    # Storage
    "DatabaseConfig",
    "RedisConfig",
    "MongoConfig",
    "PostgresTool",
    "MongoTool",
    "RedisTool",
    "S3Tool",
    "GCSStorage",
]
