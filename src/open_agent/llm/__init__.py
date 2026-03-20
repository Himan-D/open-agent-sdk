"""Multi-LLM Provider System - Support for all major LLM providers."""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Union, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import os
import structlog

logger = structlog.get_logger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"
    LOCAL = "local"
    MISTRAL = "mistral"
    COHERE = "cohere"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    streaming: bool = True
    
    @classmethod
    def from_env(cls, provider: LLMProvider) -> "LLMConfig":
        """Create config from environment variables."""
        configs = {
            LLMProvider.OPENAI: {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL"),
            },
            LLMProvider.ANTHROPIC: {
                "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            LLMProvider.GOOGLE: {
                "model": os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"),
                "api_key": os.getenv("GOOGLE_API_KEY"),
            },
            LLMProvider.NVIDIA: {
                "model": os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "base_url": os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            },
            LLMProvider.AZURE: {
                "model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
                "api_key": os.getenv("AZURE_OPENAI_KEY"),
                "base_url": os.getenv("AZURE_OPENAI_ENDPOINT"),
            },
            LLMProvider.OLLAMA: {
                "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            },
            LLMProvider.MISTRAL: {
                "model": os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
                "api_key": os.getenv("MISTRAL_API_KEY"),
                "base_url": os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"),
            },
            LLMProvider.COHERE: {
                "model": os.getenv("COHERE_MODEL", "command-r-plus"),
                "api_key": os.getenv("COHERE_API_KEY"),
            },
        }
        
        config = configs.get(provider, {})
        return cls(provider=provider, **config)


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Synchronous invoke."""
        pass
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Asynchronous invoke."""
        pass
    
    @abstractmethod
    def stream(self, messages: List[Dict[str, str]]):
        """Streaming invoke."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI GPT models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError("openai package required. Install: pip install openai")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Synchronous invoke."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Asynchronous invoke."""
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=False,
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict[str, str]]):
        """Streaming invoke."""
        client = self._get_client()
        return client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )


class AnthropicLLM(BaseLLM):
    """Anthropic Claude models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("anthropic package required. Install: pip install anthropic")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        system = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        
        response = await client.messages.create(
            model=self.config.model,
            system=system,
            messages=filtered_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.content[0].text
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        
        system = ""
        filtered_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                filtered_messages.append(msg)
        
        return client.messages.stream(
            model=self.config.model,
            system=system,
            messages=filtered_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )


class GoogleLLM(BaseLLM):
    """Google Gemini models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                self._client = genai
                if self.config.api_key:
                    genai.configure(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("google-genai package required. Install: pip install google-genai")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        contents = []
        for msg in messages:
            if msg.get("role") != "system":
                contents.append({
                    "role": "user" if msg.get("role") == "user" else "model",
                    "parts": [msg.get("content", "")]
                })
        
        response = await client.aio.models.generate_content(
            model=self.config.model,
            contents=contents,
            generation_config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            }
        )
        return response.text
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        contents = []
        for msg in messages:
            if msg.get("role") != "system":
                contents.append({
                    "role": "user" if msg.get("role") == "user" else "model",
                    "parts": [msg.get("content", "")]
                })
        return client.aio.models.generate_content_stream(
            model=self.config.model,
            contents=contents,
        )


class NVIDIAllm(BaseLLM):
    """NVIDIA NIM/MiMa models via LangChain."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._model = None
        
    def _get_model(self):
        if self._model is None:
            try:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA
                self._model = ChatNVIDIA(
                    model=self.config.model,
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError("langchain-nvidia-ai-endpoints required. Install: pip install langchain-nvidia-ai-endpoints")
        return self._model
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                langchain_messages.append(SystemMessage(content=msg.get("content", "")))
            else:
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
        
        model = self._get_model()
        response = await model.ainvoke(langchain_messages)
        return response.content
    
    def stream(self, messages: List[Dict[str, str]]):
        from langchain_core.messages import HumanMessage, SystemMessage
        
        langchain_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                langchain_messages.append(SystemMessage(content=msg.get("content", "")))
            else:
                langchain_messages.append(HumanMessage(content=msg.get("content", "")))
        
        return self._get_model().stream(langchain_messages)


class OllamaLLM(BaseLLM):
    """Ollama local models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                base_url = f"{self.config.base_url}/v1"
                self._client = AsyncOpenAI(base_url=base_url)
            except ImportError:
                raise ImportError("openai package required. Install: pip install openai")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        return client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )


class AzureLLM(BaseLLM):
    """Azure OpenAI models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncAzureOpenAI
                self._client = AsyncAzureOpenAI(
                    api_key=self.config.api_key,
                    azure_endpoint=self.config.base_url,
                    api_version="2024-02-01",
                )
            except ImportError:
                raise ImportError("openai package required. Install: pip install openai")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        return client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )


class MistralLLM(BaseLLM):
    """Mistral AI models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                raise ImportError("openai package required. Install: pip install openai")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        return client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )


class CohereLLM(BaseLLM):
    """Cohere models."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            try:
                from cohere import AsyncClientV2
                self._client = AsyncClientV2(api_key=self.config.api_key)
            except ImportError:
                raise ImportError("cohere package required. Install: pip install cohere")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        cohere_messages = []
        for msg in messages:
            if msg.get("role") != "system":
                cohere_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        system = ""
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
                break
        
        response = await client.chat(
            model=self.config.model,
            messages=cohere_messages,
            preamble=system,
        )
        return response.message.content[0].text
    
    def stream(self, messages: List[Dict[str, str]]):
        client = self._get_client()
        cohere_messages = []
        for msg in messages:
            if msg.get("role") != "system":
                cohere_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        return client.chat_stream(
            model=self.config.model,
            messages=cohere_messages,
        )


class LLMRegistry:
    """Registry for LLM providers."""
    
    _providers: Dict[LLMProvider, Type[BaseLLM]] = {
        LLMProvider.OPENAI: OpenAILLM,
        LLMProvider.ANTHROPIC: AnthropicLLM,
        LLMProvider.GOOGLE: GoogleLLM,
        LLMProvider.NVIDIA: NVIDIAllm,
        LLMProvider.OLLAMA: OllamaLLM,
        LLMProvider.AZURE: AzureLLM,
        LLMProvider.MISTRAL: MistralLLM,
        LLMProvider.COHERE: CohereLLM,
    }
    
    _models: Dict[LLMProvider, List[str]] = {
        LLMProvider.OPENAI: [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
            "gpt-3.5-turbo", "o1-preview", "o1-mini",
        ],
        LLMProvider.ANTHROPIC: [
            "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229", "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
        ],
        LLMProvider.GOOGLE: [
            "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash",
            "gemini-1.5-flash-8b", "gemini-pro", "gemini-pro-vision",
        ],
        LLMProvider.NVIDIA: [
            "nvidia/nemotron-3-super-120b-a12b",
            "nvidia/nemotron-3-ultra-405b",
            "nvidia/nemotron-3-nano-8b",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-70b-instruct",
            "mistralai/mixtral-8x7b-instruct-v0.1",
        ],
        LLMProvider.MISTRAL: [
            "mistral-large-latest", "mistral-small-latest",
            "codestral-latest", "mistral-nemo",
        ],
        LLMProvider.COHERE: [
            "command-r-plus", "command-r", "command",
            "command-light", "c4ai-command-r-plus",
        ],
    }
    
    @classmethod
    def register_provider(cls, provider: LLMProvider, llm_class: Type[BaseLLM]):
        """Register a new LLM provider."""
        cls._providers[provider] = llm_class
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        """Create an LLM instance from config."""
        provider = config.provider
        if provider not in cls._providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return cls._providers[provider](config)
    
    @classmethod
    def create_from_env(cls, provider: LLMProvider) -> BaseLLM:
        """Create an LLM from environment variables."""
        config = LLMConfig.from_env(provider)
        return cls.create(config)
    
    @classmethod
    def get_models(cls, provider: LLMProvider) -> List[str]:
        """Get available models for a provider."""
        return cls._models.get(provider, [])
    
    @classmethod
    def get_all_providers(cls) -> List[LLMProvider]:
        """Get all supported providers."""
        return list(cls._providers.keys())


def create_llm(
    provider: Union[str, LLMProvider],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> BaseLLM:
    """Create an LLM instance.
    
    Example:
        >>> llm = create_llm("openai", model="gpt-4o")
        >>> llm = create_llm("anthropic", model="claude-3-5-sonnet-20241022")
        >>> llm = create_llm("nvidia", model="nvidia/nemotron-3-super-120b-a12b")
    """
    if isinstance(provider, str):
        provider = LLMProvider(provider)
    
    config = LLMConfig(
        provider=provider,
        model=model or os.getenv(f"{provider.value.upper()}_MODEL", ""),
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return LLMRegistry.create(config)
