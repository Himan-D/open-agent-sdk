"""Auth profiles - Manages authentication credentials for model access.

Similar to OpenClaw's auth-profiles system for managing API keys and
credentials for different AI providers.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AuthProfile:
    """An authentication profile for a model provider."""
    name: str
    provider: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    priority: int = 0
    last_used: Optional[datetime] = None
    failure_count: int = 0
    cooldown_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_available(self) -> bool:
        """Check if this profile is available for use."""
        if not self.api_key:
            return False
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False
        return True

    def mark_failure(self, cooldown_seconds: int = 60) -> None:
        """Mark this profile as failed and enter cooldown."""
        self.failure_count += 1
        from datetime import timedelta
        self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)

    def mark_success(self) -> None:
        """Mark this profile as successfully used."""
        self.last_used = datetime.now()
        self.failure_count = 0
        self.cooldown_until = None


class AuthProfileStore:
    """Store for managing auth profiles."""

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = Path(store_path or "~/.open-agent/auth-profiles.json").expanduser()
        self.profiles: Dict[str, AuthProfile] = {}
        self._load()

    def _load(self) -> None:
        """Load profiles from disk."""
        if not self.store_path.exists():
            return

        try:
            data = json.loads(self.store_path.read_text())
            for name, profile_data in data.items():
                self.profiles[name] = AuthProfile(**profile_data)
            logger.info("auth_profiles_loaded", count=len(self.profiles))
        except Exception as e:
            logger.error("auth_profiles_load_error", error=str(e))

    def save(self) -> None:
        """Save profiles to disk."""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            name: {
                "name": p.name,
                "provider": p.provider,
                "api_key": p.api_key,
                "endpoint": p.endpoint,
                "priority": p.priority,
                "last_used": p.last_used.isoformat() if p.last_used else None,
                "failure_count": p.failure_count,
                "cooldown_until": p.cooldown_until.isoformat() if p.cooldown_until else None,
                "metadata": p.metadata,
            }
            for name, p in self.profiles.items()
        }
        self.store_path.write_text(json.dumps(data, indent=2))

    def add(self, profile: AuthProfile) -> None:
        """Add or update an auth profile."""
        self.profiles[profile.name] = profile
        self.save()

    def get(self, name: str) -> Optional[AuthProfile]:
        """Get an auth profile by name."""
        return self.profiles.get(name)

    def get_available(self, provider: Optional[str] = None) -> List[AuthProfile]:
        """Get all available profiles, optionally filtered by provider."""
        profiles = [
            p for p in self.profiles.values()
            if p.is_available() and (provider is None or p.provider == provider)
        ]
        return sorted(profiles, key=lambda p: (-p.priority, p.last_used or datetime.min))

    def remove(self, name: str) -> bool:
        """Remove an auth profile."""
        if name in self.profiles:
            del self.profiles[name]
            self.save()
            return True
        return False
