"""Multi-LLM Provider System - Support for all major LLM providers.

Providers: OpenAI, Anthropic, Google Gemini, NVIDIA NIM, Ollama, Azure, Mistral, Cohere, OpenRouter
"""

from __future__ import annotations

import asyncio
import os
from typing import Dict, List, Optional, Type, Union

from smith_ai.core.types import BaseLLM, LLMConfig, LLMProvider


class OpenAILLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
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


class AnthropicLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.config.api_key)
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        system, filtered = "", []
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            else:
                filtered.append(msg)
        
        response = await client.messages.create(
            model=self.config.model,
            system=system,
            messages=filtered,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.content[0].text


class GoogleLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from google import genai
            if self.config.api_key:
                genai.configure(api_key=self.config.api_key)
            self._client = genai
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        from google.genai.types import Content, Part
        client = self._get_client()
        contents = [
            Content(role="user" if m.get("role") == "user" else "model", parts=[Part(text=m.get("content", ""))])
            for m in messages if m.get("role") != "system"
        ]
        response = await client.aio.models.generate_content(model=self.config.model, contents=contents)
        return response.text or ""


class NVIDIALLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._model = None
        
    def _get_model(self):
        if self._model is None:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
            self._model = ChatNVIDIA(model=self.config.model, api_key=self.config.api_key, base_url=self.config.base_url)
        return self._model
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        lc_messages = [
            SystemMessage(content=m.get("content", "")) if m.get("role") == "system"
            else HumanMessage(content=m.get("content", ""))
            for m in messages
        ]
        response = await self._get_model().ainvoke(lc_messages)
        return response.content


class OllamaLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            base_url = f"{self.config.base_url or 'http://localhost:11434'}/v1"
            self._client = AsyncOpenAI(base_url=base_url, api_key="ollama")
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content


class AzureLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import AsyncAzureOpenAI
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.base_url,
                api_version="2024-02-01",
            )
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content


class MistralLLM(BaseLLM):
    BASE_URL = "https://api.mistral.ai/v1"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or self.BASE_URL,
            )
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content


class CohereLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from cohere import AsyncClientV2
            self._client = AsyncClientV2(api_key=self.config.api_key)
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        client = self._get_client()
        system = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
        chat_messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages if m.get("role") != "system"]
        
        response = await client.chat(model=self.config.model, messages=chat_messages, preamble=system)
        return response.message.content[0].text if hasattr(response.message.content[0], 'text') else str(response.message.content[0])


class OpenRouterLLM(BaseLLM):
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.config.base_url or self.BASE_URL,
                api_key=self.config.api_key,
            )
        return self._client
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
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


class LLMRegistry:
    """Registry for LLM providers."""
    
    _providers: Dict[LLMProvider, Type[BaseLLM]] = {
        LLMProvider.OPENAI: OpenAILLM,
        LLMProvider.ANTHROPIC: AnthropicLLM,
        LLMProvider.GOOGLE: GoogleLLM,
        LLMProvider.NVIDIA: NVIDIALLM,
        LLMProvider.OLLAMA: OllamaLLM,
        LLMProvider.AZURE: AzureLLM,
        LLMProvider.MISTRAL: MistralLLM,
        LLMProvider.COHERE: CohereLLM,
        LLMProvider.OPENROUTER: OpenRouterLLM,
    }
    
    _models: Dict[LLMProvider, List[str]] = {
        LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
        LLMProvider.GOOGLE: ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
        LLMProvider.NVIDIA: ["nvidia/nemotron-3-super-120b-a12b", "meta/llama-3.1-70b-instruct", "mistralai/mixtral-8x7b-instruct-v0.1"],
        LLMProvider.MISTRAL: ["mistral-large-latest", "mistral-small-latest", "codestral-latest"],
        LLMProvider.COHERE: ["command-r-plus", "command-r", "command"],
        LLMProvider.OLLAMA: ["llama3.2", "llama3", "mistral", "codellama"],
    }
    
    @classmethod
    def register(cls, provider: LLMProvider, llm_class: Type[BaseLLM]) -> None:
        cls._providers[provider] = llm_class
    
    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        if config.provider not in cls._providers:
            raise ValueError(f"Unsupported provider: {config.provider}")
        return cls._providers[config.provider](config)
    
    @classmethod
    def list_providers(cls) -> List[LLMProvider]:
        return list(cls._providers.keys())
    
    @classmethod
    def list_models(cls, provider: LLMProvider) -> List[str]:
        return cls._models.get(provider, [])


def create_llm(
    provider: Union[str, LLMProvider],
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLM:
    if isinstance(provider, str):
        provider = LLMProvider(provider)
    
    env_prefix = provider.value.upper()
    config = LLMConfig(
        provider=provider,
        model=model or os.getenv(f"{env_prefix}_MODEL", ""),
        api_key=api_key or os.getenv(f"{env_prefix}_API_KEY"),
        base_url=os.getenv(f"{env_prefix}_BASE_URL"),
        **kwargs
    )
    
    return LLMRegistry.create(config)


from smith_ai.core.types import LLMConfig, BaseLLM, LLMProvider

__all__ = [
    "BaseLLM",
    "LLMConfig", 
    "LLMProvider",
    "LLMRegistry",
    "create_llm",
    "OpenAILLM",
    "AnthropicLLM",
    "GoogleLLM",
    "NVIDIALLM",
    "OllamaLLM",
    "AzureLLM",
    "MistralLLM",
    "CohereLLM",
    "OpenRouterLLM",
]
