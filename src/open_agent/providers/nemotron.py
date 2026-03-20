"""NVIDIA Nemotron model provider.

This module provides integration with NVIDIA Nemotron models via
langchain-nvidia-ai-endpoints.
"""

from typing import Optional, Any, List
import structlog
import os

logger = structlog.get_logger(__name__)


class NemotronProvider:
    """NVIDIA Nemotron model provider.
    
    Provides access to NVIDIA Nemotron models through the langchain library.
    Supports various Nemotron models including:
    - nemotron-3-super-120b-a12b
    - nemotron-4-340b-a12b
    - nemotron-4-mini-a12b
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "nvidia/nemotron-3-super-120b-a12b",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = None

    def initialize(self) -> None:
        """Initialize the model."""
        if self.model is not None:
            return

        try:
            from langchain_nvidia_ai_endpoints import ChatNVIDIA
            
            self.model = ChatNVIDIA(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            logger.info("nemotron_initialized", model=self.model_name)
        except ImportError:
            logger.error("langchain_nvidia_ai_endpoints_not_installed")
            raise ImportError(
                "langchain-nvidia-ai-endpoints is required. "
                "Install with: pip install langchain-nvidia-ai-endpoints"
            )

    async def invoke(self, messages: List[Any]) -> Any:
        """Invoke the model with messages."""
        if self.model is None:
            self.initialize()

        return await self.model.ainvoke(messages)

    async def ainvoke(self, messages: List[Any]) -> Any:
        """Async invoke the model with messages."""
        return await self.invoke(messages)

    def invoke_sync(self, messages: List[Any]) -> Any:
        """Synchronously invoke the model."""
        if self.model is None:
            self.initialize()

        return self.model.invoke(messages)


_global_provider: Optional[NemotronProvider] = None


def create_nemotron_model(
    model_name: str = "nvidia/nemotron-3-super-120b-a12b",
    temperature: float = 0.7,
    api_key: Optional[str] = None,
) -> NemotronProvider:
    """Create or get the global Nemotron provider."""
    global _global_provider
    
    if _global_provider is None:
        _global_provider = NemotronProvider(
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
        )
        _global_provider.initialize()
    
    return _global_provider


def get_nemotron_model() -> Optional[NemotronProvider]:
    """Get the global Nemotron provider if available."""
    return _global_provider
