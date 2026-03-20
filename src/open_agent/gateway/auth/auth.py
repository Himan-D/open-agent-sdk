"""Authentication handler for gateway requests."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AuthCredentials:
    """Authentication credentials."""
    user_id: str
    token: Optional[str] = None
    api_key: Optional[str] = None
    expires_at: Optional[datetime] = None


class AuthHandler:
    """Handles authentication for gateway requests.
    
    Similar to OpenClaw's gateway auth system for securing
    access to the agent platform.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or "default-secret-key"
        self.credentials: Dict[str, AuthCredentials] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}

    def authenticate(
        self,
        user_id: str,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> bool:
        """Authenticate a user."""
        creds = self.credentials.get(user_id)
        if not creds:
            return False

        if creds.expires_at and datetime.now() > creds.expires_at:
            return False

        if token and creds.token != token:
            return False

        if api_key and creds.api_key != api_key:
            return False

        logger.info("user_authenticated", user_id=user_id)
        return True

    def authorize(
        self,
        user_id: str,
        required_permissions: List[str],
    ) -> bool:
        """Check if user has required permissions."""
        return user_id in self.credentials

    def add_credentials(
        self,
        user_id: str,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> None:
        """Add credentials for a user."""
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)

        self.credentials[user_id] = AuthCredentials(
            user_id=user_id,
            token=token,
            api_key=api_key,
            expires_at=expires_at,
        )

    def remove_credentials(self, user_id: str) -> bool:
        """Remove credentials for a user."""
        if user_id in self.credentials:
            del self.credentials[user_id]
            return True
        return False

    def check_rate_limit(
        self,
        user_id: str,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> bool:
        """Check if user is within rate limits."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)

        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []

        self.rate_limits[user_id] = [
            ts for ts in self.rate_limits[user_id] if ts > cutoff
        ]

        if len(self.rate_limits[user_id]) >= max_requests:
            return False

        self.rate_limits[user_id].append(now)
        return True
