"""LLM Providers - OpenRouter, OpenAI, Anthropic, NVIDIA, Google, Ollama."""

from __future__ import annotations

import os
from typing import Optional, List, Dict, Any
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class LLMProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
    COHERE = "cohere"


class BaseLLM:
    """Base class for all LLM providers."""
    
    def __init__(self, api_key: str = None, model: str = "", **kwargs):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.kwargs = kwargs
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Async invoke - implement in subclass."""
        raise NotImplementedError
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Sync invoke."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.ainvoke(messages))
        except RuntimeError:
            return asyncio.run(self.ainvoke(messages))


class OpenRouterLLM(BaseLLM):
    """OpenRouter - Unified API for 100+ models.
    
    Supports: GPT-4, Claude, Mistral, Llama, Gemini, and many more.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    MODELS = [
        "openai/gpt-4-turbo",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-opus",
        "meta-llama/llama-3-70b-instruct",
        "mistralai/mixtral-8x7b-instruct",
        "google/gemini-pro-1.5",
        "deepseek-ai/deepseek-coder-33b-instruct",
    ]
    
    def __init__(self, api_key: str = None, model: str = "openai/gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.BASE_URL,
                api_key=self.api_key,
            )
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        return response.choices[0].message.content
    
    def list_models(self) -> List[str]:
        """List available models."""
        return self.MODELS


class OpenAILLM(BaseLLM):
    """OpenAI GPT models."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content


class AnthropicLLM(BaseLLM):
    """Anthropic Claude models."""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        
        system = ""
        filtered = []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                filtered.append(msg)
        
        response = await client.messages.create(
            model=self.model,
            system=system,
            messages=filtered,
            temperature=self.temperature,
            max_tokens=self.kwargs.get("max_tokens", 4096),
        )
        
        return response.content[0].text


class GoogleLLM(BaseLLM):
    """Google Gemini models."""
    
    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash-exp", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from google import genai
            genai.configure(api_key=self.api_key)
            self._client = genai
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        from google.genai.types import Content, Part
        
        contents = []
        for msg in messages:
            if msg.get("role") != "system":
                contents.append(Content(
                    role="user" if msg.get("role") == "user" else "model",
                    parts=[Part(text=msg.get("content", ""))]
                ))
        
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=contents,
        )
        
        return response.text


class NVIDIAChatLLM(BaseLLM):
    """NVIDIA NIM/MiMa models via LangChain."""
    
    def __init__(self, api_key: str = None, model: str = "nvidia/nemotron-3-super-120b-a12b", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
            self._client = ChatNVIDIA(
                model=self.model,
                api_key=self.api_key,
            )
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        lc_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                lc_messages.append(SystemMessage(content=msg.get("content", "")))
            else:
                lc_messages.append(HumanMessage(content=msg.get("content", "")))
        
        response = await self._get_client().ainvoke(lc_messages)
        return response.content


class OllamaLLM(BaseLLM):
    """Ollama local models."""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(None, model, **kwargs)
        self.model = model
        self.base_url = base_url
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(base_url=f"{self.base_url}/v1", api_key="ollama")
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content


class MistralLLM(BaseLLM):
    """Mistral AI models."""
    
    BASE_URL = "https://api.mistral.ai/v1"
    
    def __init__(self, api_key: str = None, model: str = "mistral-large-latest", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self.model = model
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.BASE_URL,
                api_key=self.api_key,
            )
        return self._client
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content


class LLMRegistry:
    """Registry for LLM providers."""
    
    _providers: Dict[str, type] = {
        "openrouter": OpenRouterLLM,
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        "google": GoogleLLM,
        "nvidia": NVIDIAChatLLM,
        "ollama": OllamaLLM,
        "mistral": MistralLLM,
    }
    
    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseLLM:
        """Create LLM instance."""
        provider = provider.lower()
        
        if provider not in cls._providers:
            available = list(cls._providers.keys())
            raise ValueError(f"Unknown provider: {provider}. Available: {available}")
        
        return cls._providers[provider](**kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List available providers."""
        return list(cls._providers.keys())
    
    @classmethod
    def register(cls, name: str, llm_class: type):
        """Register custom provider."""
        cls._providers[name] = llm_class


def create_llm(
    provider: str = "openai",
    api_key: str = None,
    model: str = None,
    **kwargs
) -> BaseLLM:
    """Create LLM instance.
    
    Examples:
        >>> llm = create_llm("openai", model="gpt-4o")
        >>> llm = create_llm("openrouter", api_key="...", model="anthropic/claude-3-5-sonnet")
        >>> llm = create_llm("nvidia", model="nvidia/nemotron-3-super-120b-a12b")
    """
    # Set default models
    defaults = {
        "openai": "gpt-4o-mini",
        "openrouter": "openai/gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "google": "gemini-2.0-flash-exp",
        "nvidia": "nvidia/nemotron-3-super-120b-a12b",
        "ollama": "llama3.2",
        "mistral": "mistral-large-latest",
    }
    
    if model is None:
        model = defaults.get(provider.lower(), "gpt-4o-mini")
    
    return LLMRegistry.create(provider, api_key=api_key, model=model, **kwargs)
