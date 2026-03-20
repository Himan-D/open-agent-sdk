"""Configuration management for OpenAgent."""

from typing import Optional
from pydantic import Field
from functools import lru_cache


class NVIDIAConfig:
    """NVIDIA API configuration."""
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        model: str = "nvidia/nemotron-3-super-120b-a12b",
    ):
        import os
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.base_url = base_url
        self.model = model


class OpenShellConfig:
    """OpenShell sandbox configuration."""
    def __init__(
        self,
        enabled: bool = True,
        sandbox_type: str = "auto",
        policy_file: Optional[str] = None,
        credential_provider: str = "nvidia",
        remote_host: Optional[str] = None,
    ):
        import os
        self.enabled = enabled
        self.sandbox_type = sandbox_type
        self.policy_file = policy_file
        self.credential_provider = credential_provider
        self.remote_host = remote_host or os.environ.get("OPENSHELL_REMOTE_HOST")


class AgentConfig:
    """Agent configuration."""
    def __init__(
        self,
        name: str = "open-agent",
        model: str = "nvidia/nemotron-3-super-120b-a12b",
        model_provider: str = "nvidia",
        max_iterations: int = 50,
        max_retries: int = 6,
        timeout: int = 300,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        import os
        self.name = name
        self.model = model or os.environ.get("AGENT_MODEL", model)
        self.model_provider = model_provider
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self.timeout = timeout
        self.temperature = temperature
        self.system_prompt = system_prompt


class MemoryConfig:
    """Memory persistence configuration."""
    def __init__(
        self,
        enabled: bool = True,
        backend: str = "store",
        storage_path: str = "./memory",
        max_long_term: int = 1000,
    ):
        self.enabled = enabled
        self.backend = backend
        self.storage_path = storage_path
        self.max_long_term = max_long_term


class OpenAgentConfig:
    """Main OpenAgent configuration."""
    def __init__(
        self,
        nvidia: Optional[NVIDIAConfig] = None,
        openshell: Optional[OpenShellConfig] = None,
        agent_config: Optional[AgentConfig] = None,
        memory: Optional[MemoryConfig] = None,
    ):
        self.nvidia = nvidia or NVIDIAConfig()
        self.openshell = openshell or OpenShellConfig()
        self.agent_config = agent_config or AgentConfig()
        self.memory = memory or MemoryConfig()


_config_instance: Optional[OpenAgentConfig] = None


@lru_cache
def get_config() -> OpenAgentConfig:
    """Get cached configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = OpenAgentConfig()
    return _config_instance


def load_config_from_file(config_path: str) -> OpenAgentConfig:
    """Load configuration from a YAML file."""
    import yaml
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    return OpenAgentConfig(**data)
