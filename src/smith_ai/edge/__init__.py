"""Edge AI - Local LLM support for on-device inference.

Supports:
- Ollama API (Llama, Mistral, Phi, etc.)
- Llama.cpp via server mode
- Hugging Face Transformers
- GGUF quantized models
- TGI (Text Generation Inference)
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)

try:
    import httpx
except ImportError:
    httpx = None


class ModelSize(Enum):
    """Model size categories."""
    TINY = "tiny"       # < 1B params (Phi-2, TinyLlama)
    SMALL = "small"     # 1-3B params (Llama 3.2 1B, Phi-3)
    MEDIUM = "medium"   # 3-7B params (Llama 3.2 3B, Mistral 7B)
    LARGE = "large"     # 7-13B params (Llama 3.1 8B, Qwen 7B)
    XL = "xl"           # 13-70B params (Llama 3.1 70B, Mixtral)
    XXL = "xxl"         # > 70B params (Llama 3.1 405B)


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    size: ModelSize
    size_gb: float
    quantization: str
    context_length: int
    recommended_ram: str
    use_cases: List[str]


@dataclass
class OllamaConfig:
    """Configuration for Ollama."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    num_ctx: int = 4096
    num_gpu: int = 0
    num_thread: int = 0


class OllamaClient:
    """Client for Ollama API.
    
    Ollama runs local LLMs on your machine. Supports:
    - Llama 3.1, 3.2
    - Mistral, Mixtral
    - Phi-3, Phi-4
    - Qwen 2.5
    - Gemma 2
    - And 100+ other models
    
    Real use cases:
    - Privacy-sensitive applications
    - Offline operation
    - Cost reduction
    - Low latency for small tasks
    - Experimentation without API costs
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.base_url = self.config.base_url
        self.model = self.config.model
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120)
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.json().get("models", [])
        except Exception as e:
            logger.error("ollama_list_models_failed", error=str(e))
            return []
    
    async def pull_model(self, name: str, stream: bool = True) -> AsyncIterator[str]:
        """Pull a model from Ollama registry."""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/pull",
            json={"name": name, "stream": stream}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "status" in data:
                            yield data["status"]
                    except json.JSONDecodeError:
                        pass
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        options: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate text (non-streaming)."""
        data = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system:
            data["system"] = system
        if template:
            data["template"] = template
        if context:
            data["context"] = context
        
        options = options or {}
        options.setdefault("temperature", self.config.temperature)
        options.setdefault("top_p", self.config.top_p)
        options.setdefault("top_k", self.config.top_k)
        data["options"] = options
        
        response = await self.client.post(f"{self.base_url}/api/generate", json=data)
        return response.json()
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        options: Optional[Dict] = None,
    ) -> AsyncIterator[str]:
        """Generate text with streaming."""
        data = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": True,
        }
        
        if system:
            data["system"] = system
        
        options = options or {}
        options.setdefault("temperature", self.config.temperature)
        data["options"] = options
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=data
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Chat completion (for models that support it)."""
        data = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        
        if tools:
            data["tools"] = tools
        
        try:
            response = await self.client.post(f"{self.base_url}/api/chat", json=data)
            return response.json()
        except Exception as e:
            logger.error("ollama_chat_failed", error=str(e))
            return {"message": {"content": f"Error: {str(e)}"}}
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Chat with streaming."""
        data = {
            "model": model or self.model,
            "messages": messages,
            "stream": True,
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=data
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass
    
    async def embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """Get embeddings for text."""
        data = {
            "model": model or self.model,
            "prompt": text,
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/embeddings", json=data)
            return response.json().get("embedding", [])
        except Exception as e:
            logger.error("ollama_embeddings_failed", error=str(e))
            return []
    
    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False


class LlamaCppServer:
    """Client for Llama.cpp server mode.
    
    Llama.cpp provides efficient inference for quantized models:
    - GGUF format models
    - CPU and GPU inference
    - Multiple quantization levels (Q2, Q4, Q5, Q8)
    
    Run: ./server -m model.gguf -c 4096
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=300)
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
    
    async def completion(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get completion."""
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if stop:
            data["stop"] = stop
        
        try:
            response = await self.client.post(
                f"{self.base_url}/completion",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"content": f"Error: {str(e)}", "error": True}
    
    async def completion_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream completion."""
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/completion",
            json=data
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "content" in chunk:
                            yield chunk["content"]
                        if chunk.get("stop"):
                            break
                    except json.JSONDecodeError:
                        pass


class TransformersLocal:
    """Local inference using Hugging Face Transformers.
    
    For when you need maximum control over model loading.
    Supports PyTorch, TensorFlow, and JAX backends.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/Phi-3-mini-128k-instruct",
        device: str = "cpu",
        torch_dtype: str = "float16",
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
    ):
        self.model_name = model_name
        self.device = device
        self.torch_dtype = torch_dtype
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self._pipeline = None
        self._model = None
        self._tokenizer = None
    
    async def load(self) -> None:
        """Load model and tokenizer."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            kwargs = {"device_map": self.device}
            
            if self.load_in_4bit:
                kwargs["load_in_4bit"] = True
            elif self.load_in_8bit:
                kwargs["load_in_8bit"] = True
            
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **kwargs
            )
            
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
            )
            
            logger.info("transformers_model_loaded", model=self.model_name)
        
        except ImportError:
            logger.error("transformers_not_installed")
            raise ImportError("transformers not installed. Run: pip install transformers torch")
    
    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """Generate text."""
        if not self._pipeline:
            await self.load()
        
        outputs = self._pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
        )
        
        return outputs[0]["generated_text"]
    
    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings."""
        if not self._tokenizer:
            await self.load()
        
        from transformers import AutoModel
        import torch
        
        model = AutoModel.from_pretrained(self.model_name)
        model.to(self.device)
        
        embeddings = []
        for text in texts:
            inputs = self._tokenizer(text, return_tensors="pt", truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Mean pooling
                embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
            
            embeddings.append(embedding)
        
        return embeddings
    
    def unload(self) -> None:
        """Free memory."""
        del self._model
        del self._tokenizer
        del self._pipeline
        self._model = None
        self._tokenizer = None
        self._pipeline = None


class TGIClient:
    """Client for Text Generation Inference (TGI) server.
    
    TGI is Hugging Face's production-grade inference server:
    - Flash Attention
    - Paged Attention
    - Continuous batching
    - Quantization (AWQ, GPTQ)
    - Speculative decoding
    
    Run: docker run -d --gpus all -p 8080:80 ghcr.io/huggingface/text-generation-inference:latest --model-id meta-llama/Llama-3.1-8B-Instruct
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=300)
        return self._client
    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
    
    async def generate(
        self,
        inputs: str,
        model: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        return_full_text: bool = False,
    ) -> Dict[str, Any]:
        """Generate with TGI."""
        data = {
            "inputs": inputs,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
                "return_full_text": return_full_text,
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/generate",
                json=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def generate_stream(
        self,
        inputs: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream generation."""
        data = {
            "inputs": inputs,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "stream": True,
            }
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/generate",
            json=data
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "token" in chunk:
                            yield chunk["token"].get("text", "")
                    except json.JSONDecodeError:
                        pass
    
    async def info(self) -> Dict[str, Any]:
        """Get model info."""
        try:
            response = await self.client.get(f"{self.base_url}/info")
            return response.json()
        except:
            return {}


@dataclass
class EdgeDeploymentConfig:
    """Configuration for edge deployment."""
    device: str = "cpu"  # cpu, cuda, mps
    quantization: str = "int8"  # int4, int8, float16, float32
    batch_size: int = 1
    max_concurrent_requests: int = 1
    cache_dir: Optional[str] = None
    prefer_cpu: bool = False


class LocalModelFactory:
    """Factory for creating local LLM instances."""
    
    @staticmethod
    def create(
        backend: str = "ollama",
        model: str = "llama3.2",
        **kwargs
    ) -> Union[OllamaClient, LlamaCppServer, TransformersLocal, TGIClient]:
        """Create a local model client.
        
        Args:
            backend: "ollama", "llama.cpp", "transformers", "tgi"
            model: Model name/path
            **kwargs: Backend-specific options
        
        Returns:
            Local model client
        """
        backends = {
            "ollama": lambda: OllamaClient(OllamaConfig(model=model, **kwargs)),
            "llama.cpp": lambda: LlamaCppServer(base_url=kwargs.get("base_url", "http://localhost:8080")),
            "transformers": lambda: TransformersLocal(model_name=model, **kwargs),
            "tgi": lambda: TGIClient(base_url=kwargs.get("base_url", "http://localhost:8080")),
        }
        
        creator = backends.get(backend.lower())
        if not creator:
            raise ValueError(f"Unknown backend: {backend}. Choose from: {list(backends.keys())}")
        
        return creator()
    
    @staticmethod
    def recommended_models() -> List[ModelInfo]:
        """Get recommended models for different use cases."""
        return [
            ModelInfo(
                name="llama3.2:1b",
                size=ModelSize.SMALL,
                size_gb=0.8,
                quantization="Q4_K_M",
                context_length=128000,
                recommended_ram="2GB",
                use_cases=["mobile", "edge", "quick_tasks"]
            ),
            ModelInfo(
                name="llama3.2:3b",
                size=ModelSize.MEDIUM,
                size_gb=2.0,
                quantization="Q4_K_M",
                context_length=128000,
                recommended_ram="6GB",
                use_cases=["general", "chat", "coding"]
            ),
            ModelInfo(
                name="llama3.1:8b",
                size=ModelSize.LARGE,
                size_gb=4.7,
                quantization="Q4_K_M",
                context_length=128000,
                recommended_ram="16GB",
                use_cases=["production", "reasoning", "long_context"]
            ),
            ModelInfo(
                name="mistral:7b",
                size=ModelSize.MEDIUM,
                size_gb=4.1,
                quantization="Q4_K_M",
                context_length=32768,
                recommended_ram="8GB",
                use_cases=["instruction_following", "agents"]
            ),
            ModelInfo(
                name="phi3:3.8b",
                size=ModelSize.MEDIUM,
                size_gb=2.3,
                quantization="Q4_K_M",
                context_length=4096,
                recommended_ram="4GB",
                use_cases=["code", "reasoning", "constrained"]
            ),
            ModelInfo(
                name="qwen2.5:7b",
                size=ModelSize.MEDIUM,
                size_gb=4.4,
                quantization="Q4_K_M",
                context_length=32768,
                recommended_ram="8GB",
                use_cases=["chat", "multilingual", "agents"]
            ),
            ModelInfo(
                name="nomic-embed-text",
                size=ModelSize.TINY,
                size_gb=0.27,
                quantization="Q8",
                context_length=8192,
                recommended_ram="1GB",
                use_cases=["embeddings", "search", "RAG"]
            ),
        ]


__all__ = [
    "OllamaClient",
    "OllamaConfig",
    "LlamaCppServer",
    "TransformersLocal",
    "TGIClient",
    "LocalModelFactory",
    "EdgeDeploymentConfig",
    "ModelSize",
    "ModelInfo",
]
