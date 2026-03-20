"""NVIDIA Nemotron model integration via LangChain NVIDIA AI Endpoints.

This module provides integration with NVIDIA Nemotron models using the
official langchain-nvidia-ai-endpoints package.
"""

from typing import Optional, Dict, Any, List, Union, Callable
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from open_agent.config.settings import get_config


def create_nemotron_model(
    model_name: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> BaseChatModel:
    """Create a configured Nemotron chat model via LangChain.

    Uses langchain-nvidia-ai-endpoints for official NVIDIA integration.

    Example:
        >>> from open_agent.models.nemotron import create_nemotron_model
        >>>
        >>> model = create_nemotron_model(
        ...     model_name="nvidia/nemotron-3-super-120b-a12b",
        ...     temperature=0.7
        ... )
    """
    try:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        config = get_config()
        model_id = model_name or config.nvidia.model

        # Check if using hosted API or self-hosted NIM
        if base_url:
            llm = ChatNVIDIA(
                model=model_id,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            llm = ChatNVIDIA(
                model=model_id,
                api_key=api_key or config.nvidia.api_key,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return llm

    except ImportError:
        raise ImportError(
            "langchain-nvidia-ai-endpoints is required for Nemotron integration. "
            "Install with: pip install langchain-nvidia-ai-endpoints"
        )


@lru_cache
def get_nemotron_model(
    model_name: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """Get a cached Nemotron model instance."""
    return create_nemotron_model(
        model_name=model_name,
        temperature=temperature,
    )


def get_available_nemotron_models() -> List[str]:
    """Get list of available Nemotron models on NVIDIA API."""
    return [
        "nvidia/nemotron-3-super-120b-a12b",
        "nvidia/nemotron-3-ultra-405b",
        "nvidia/nemotron-3-nano-8b",
        "nvidia/Nemotron-Nano-3-30B-A3B-FP8",
        "nvidia/Nemotron-Nano-3-30B-A3B-BF16",
    ]


class NemotronModel:
    """High-level wrapper for Nemotron model with additional features.

    This class provides a simpler interface for common use cases while
    maintaining access to the underlying LangChain model.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
    ):
        self.model = create_nemotron_model(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )
        self.model_name = model_name or get_config().nvidia.model

    def invoke(self, prompt: str) -> str:
        """Simple invoke call."""
        from langchain_core.messages import HumanMessage
        result = self.model.invoke([HumanMessage(content=prompt)])
        return result.content

    def stream(self, prompt: str):
        """Streaming invoke call."""
        from langchain_core.messages import HumanMessage
        return self.model.stream([HumanMessage(content=prompt)])

    def with_tools(self, tools: List[Any]) -> "NemotronModel":
        """Bind tools to the model for tool-calling support."""
        self.model = self.model.bind_tools(tools)
        return self
