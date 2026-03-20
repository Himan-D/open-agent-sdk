"""OpenAgent - Multi-model AI agent orchestration framework.

Built with:
- LangChain Deep Agents for agentic workflows
- NVIDIA Nemotron for reasoning
- NVIDIA OpenShell for secure sandboxed execution
- OpenClaw-inspired architecture for multi-agent orchestration

Example:
    >>> from open_agent import create_deep_agent, create_gateway
    >>>
    >>> # Create an agent
    >>> agent = create_deep_agent(
    ...     name="my-agent",
    ...     model="nvidia/nemotron-3-super-120b-a12b"
    ... )
    >>>
    >>> # Process a message
    >>> response = await agent.process_message("Hello!")

Version:
    1.0.0 - Production stable
"""

from __future__ import annotations

__version__: str = "1.0.0"
__status__: str = "production"

from open_agent.core.gateway import Gateway, create_gateway, Channel, Binding, Session
from open_agent.core.health import HealthChecker, HealthStatus, HealthCheck, create_health_checker
from open_agent.core.types import (
    BaseAgent,
    AgentConfig,
    AgentContext,
    Message,
    ToolCall,
    ToolResult,
    PermissionLevel,
    SessionState,
)

from open_agent.agents import (
    DeepAgent,
    BaseTool,
    ToolResult,
    ToolCall,
    SoulConfig,
    AgentContext,
    Message,
    ShellTool,
    FileTools,
    TodoTool,
)
from open_agent.agents.tools.base import ToolRegistry
from open_agent.agents.auth import AuthProfile, AuthProfileStore
from open_agent.agents.runtime import create_deep_agent

from open_agent.models.nemotron import (
    NemotronModel,
    create_nemotron_model,
    get_available_nemotron_models,
)
from open_agent.providers import NemotronProvider, create_nemotron_model

from open_agent.backends.openshell import (
    OpenShellBackend,
    SandboxSession,
    SandboxType,
    create_openshell_backend,
    get_default_backend,
)

from open_agent.memory.memory import (
    MemoryStore,
    MemoryEntry,
    create_memory_store,
)

from open_agent.tools.skills import (
    Skill,
    SkillRegistry,
    SkillInvocation,
    create_skill_registry,
)

from open_agent.channels.channel_manager import (
    ChannelManager,
    ChannelType,
    ChannelConfig,
    BaseChannel,
    SlackChannel,
    DiscordChannel,
    TelegramChannel,
    WebSocketChannel,
    create_channel_manager,
)

from open_agent.ui.tui import (
    TUI,
    TUIPanel,
    PanelType,
    start_tui,
)

from open_agent.config.settings import (
    OpenAgentConfig,
    AgentConfig,
    MemoryConfig,
    NVIDIAConfig,
    OpenShellConfig,
    get_config,
    load_config_from_file,
)

from open_agent.config.secrets import (
    SecretsManager,
    Secret,
    create_secrets_manager,
)

from open_agent.gateway import MessageRouter, SessionManager, AuthHandler
from open_agent.channels import ChannelRegistry, Transport
from open_agent.channels.transport.base import TransportConfig
from open_agent.channels.additional import (
    ChannelPlatform,
    ChannelMessage,
    ChannelCredentials,
    WhatsAppChannel,
    SignalChannel,
    IRCChannel,
    MattermostChannel,
    MatrixChannel,
    NostrChannel,
    ChannelFactory,
)
from open_agent.plugins import PluginManager, Plugin

# Voice modules
from open_agent.voice import TextToSpeech, SpeechToText, TTSEngine, STTEngine
from open_agent.voice.tts import VoiceConfig, SpeechResult, create_tts_engine
from open_agent.voice.stt import STTConfig, TranscriptionResult, create_stt_engine

# Canvas modules
from open_agent.canvas import Canvas, CanvasFile, CanvasSession, create_canvas

# Browser sandbox
from open_agent.sandbox import BrowserSandbox, BrowserConfig, create_browser_sandbox

__all__: list[str] = [
    "__version__",
    "Gateway",
    "create_gateway",
    "Channel",
    "Binding",
    "Session",
    "HealthChecker",
    "HealthStatus",
    "HealthCheck",
    "create_health_checker",
    "DeepAgent",
    "create_deep_agent",
    "SoulConfig",
    "AgentContext",
    "Message",
    "ToolCall",
    "ToolResult",
    "Skill",
    "BaseTool",
    "ShellTool",
    "FileTools",
    "TodoTool",
    "ToolRegistry",
    "PermissionLevel",
    "NemotronModel",
    "NemotronProvider",
    "create_nemotron_model",
    "get_available_nemotron_models",
    "OpenShellBackend",
    "SandboxSession",
    "SandboxType",
    "create_openshell_backend",
    "get_default_backend",
    "MemoryStore",
    "MemoryEntry",
    "create_memory_store",
    "SkillRegistry",
    "SkillInvocation",
    "create_skill_registry",
    "ChannelManager",
    "ChannelType",
    "ChannelConfig",
    "BaseChannel",
    "SlackChannel",
    "DiscordChannel",
    "TelegramChannel",
    "WebSocketChannel",
    "create_channel_manager",
    "TUI",
    "TUIPanel",
    "PanelType",
    "start_tui",
    "OpenAgentConfig",
    "AgentConfig",
    "MemoryConfig",
    "NVIDIAConfig",
    "OpenShellConfig",
    "get_config",
    "load_config_from_file",
    "SecretsManager",
    "Secret",
    "create_secrets_manager",
    "MessageRouter",
    "SessionManager",
    "AuthHandler",
    "ChannelRegistry",
    "Transport",
    "TransportConfig",
    "PluginManager",
    "Plugin",
    "AuthProfile",
    "AuthProfileStore",
    # Additional channels
    "ChannelPlatform",
    "ChannelMessage",
    "ChannelCredentials",
    "WhatsAppChannel",
    "SignalChannel",
    "IRCChannel",
    "MattermostChannel",
    "MatrixChannel",
    "NostrChannel",
    "ChannelFactory",
    # Voice
    "TextToSpeech",
    "SpeechToText",
    "TTSEngine",
    "STTEngine",
    "VoiceConfig",
    "SpeechResult",
    "TranscriptionResult",
    "create_tts_engine",
    "create_stt_engine",
    # Canvas
    "Canvas",
    "CanvasFile",
    "CanvasSession",
    "create_canvas",
    # Browser sandbox
    "BrowserSandbox",
    "BrowserConfig",
    "create_browser_sandbox",
]