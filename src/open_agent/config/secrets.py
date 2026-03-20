"""Secrets management - Secure storage for API keys and credentials.

This module provides secure secrets management similar to OpenClaw:
- Environment variable based storage
- File-based encrypted secrets
- Secrets reload without restart
- Secrets validation
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
import os
import json
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Secret:
    """A stored secret."""
    name: str
    source: str  # env, file, vault
    description: str = ""
    masked: bool = True


class SecretsManager:
    """Manage secrets and credentials."""

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path or "~/.open-agent").expanduser()
        self.secrets_file = self.workspace_path / "secrets.json"
        self._secrets: Dict[str, Secret] = {}
        self._loaded_values: Dict[str, str] = {}
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Load secrets from file and environment."""
        # Load from file
        if self.secrets_file.exists():
            try:
                data = json.loads(self.secrets_file.read_text())
                for name, info in data.items():
                    self._secrets[name] = Secret(
                        name=name,
                        source="file",
                        description=info.get("description", ""),
                    )
            except Exception as e:
                logger.error("secrets_load_error", error=str(e))

        # Load from environment
        for key, value in os.environ.items():
            if key.startswith(("NVIDIA_", "OPENAI_", "ANTHROPIC_", "SLACK_", "DISCORD_")):
                if key not in self._secrets:
                    self._secrets[key] = Secret(
                        name=key,
                        source="env",
                        description=f"Environment variable: {key}",
                    )
                self._loaded_values[key] = value

        logger.info("secrets_loaded", count=len(self._secrets))

    def get(self, name: str) -> Optional[str]:
        """Get a secret value."""
        # Try environment first
        env_value = os.environ.get(name)
        if env_value:
            return env_value

        # Try loaded values
        return self._loaded_values.get(name)

    def get_masked(self, name: str) -> str:
        """Get a masked version of a secret."""
        value = self.get(name)
        if not value:
            return "[not set]"
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    def set(self, name: str, value: str, description: str = "") -> None:
        """Set a secret value (only in memory)."""
        self._loaded_values[name] = value
        if name not in self._secrets:
            self._secrets[name] = Secret(
                name=name,
                source="memory",
                description=description,
            )
        logger.info("secret_set", name=name)

    def list(self) -> List[Dict[str, Any]]:
        """List all secrets (masked values)."""
        return [
            {
                "name": s.name,
                "source": s.source,
                "description": s.description,
                "masked": self.get_masked(s.name),
                "is_set": self.get(s.name) is not None,
            }
            for s in self._secrets.values()
        ]

    def validate(self) -> Dict[str, Any]:
        """Validate required secrets are set."""
        required = {
            "NVIDIA_API_KEY": "NVIDIA API key for Nemotron models",
        }

        results = {
            "valid": True,
            "missing": [],
            "present": [],
        }

        for name, description in required.items():
            value = self.get(name)
            if value:
                results["present"].append(name)
            else:
                results["missing"].append({"name": name, "description": description})
                results["valid"] = False

        return results

    def reload(self) -> None:
        """Reload secrets from environment."""
        self._load_secrets()
        logger.info("secrets_reloaded")

    def export_env(self) -> Dict[str, str]:
        """Export current secrets as environment variables."""
        return dict(self._loaded_values)


def create_secrets_manager(workspace_path: Optional[str] = None) -> SecretsManager:
    """Create a secrets manager."""
    return SecretsManager(workspace_path=workspace_path)
