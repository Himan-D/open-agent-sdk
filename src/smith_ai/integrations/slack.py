"""Slack integration for SmithAI.

Provides:
- Messaging
- Channel management
- Webhooks
- Workflows
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class SlackConfig:
    token: str
    signing_secret: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "SlackConfig":
        return cls(
            token=os.environ.get("SLACK_BOT_TOKEN", ""),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )


class SlackClient:
    """Slack API client.
    
    Real use cases:
    - Send alerts
    - Create incidents
    - Post updates
    - Manage channels
    - Team notifications
    """
    
    API_URL = "https://slack.com/api"
    
    def __init__(self, config: Optional[SlackConfig] = None):
        self.config = config or SlackConfig.from_env()
        self._token = self.config.token
    
    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Post a message to a channel."""
        if not httpx:
            return {"ok": False, "error": "httpx not installed"}
        
        data = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/chat.postMessage",
                headers={"Authorization": f"Bearer {self._token}"},
                data=data
            )
            return response.json()
    
    async def post_ephemeral(
        self,
        channel: str,
        user: str,
        text: str,
    ) -> Dict[str, Any]:
        """Post an ephemeral message to a user."""
        if not httpx:
            return {"ok": False, "error": "httpx not installed"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/chat.postEphemeral",
                headers={"Authorization": f"Bearer {self._token}"},
                data={
                    "channel": channel,
                    "user": user,
                    "text": text,
                }
            )
            return response.json()
    
    async def upload_file(
        self,
        channel: str,
        file_path: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to Slack."""
        if not httpx:
            return {"ok": False, "error": "httpx not installed"}
        
        with open(file_path, "rb") as f:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/files.upload",
                    headers={"Authorization": f"Bearer {self._token}"},
                    data={
                        "channel": channel,
                        "title": title or os.path.basename(file_path),
                        "initial_comment": initial_comment,
                    },
                    files={"file": f}
                )
                return response.json()
    
    async def list_channels(self) -> List[Dict[str, Any]]:
        """List all channels."""
        if not httpx:
            return []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/conversations.list",
                headers={"Authorization": f"Bearer {self._token}"},
                params={"types": "public_channel,private_channel"}
            )
            data = response.json()
            return data.get("channels", [])
    
    async def create_channel(
        self,
        name: str,
        is_private: bool = False,
    ) -> Dict[str, Any]:
        """Create a channel."""
        if not httpx:
            return {"ok": False}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/conversations.create",
                headers={"Authorization": f"Bearer {self._token}"},
                data={
                    "name": name,
                    "is_private": is_private,
                }
            )
            return response.json()
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user info."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.API_URL}/users.info",
                headers={"Authorization": f"Bearer {self._token}"},
                params={"user": user_id}
            )
            return response.json().get("user", {})
    
    async def open_dm(self, user_id: str) -> Dict[str, Any]:
        """Open a direct message with a user."""
        if not httpx:
            return {"ok": False}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/conversations.open",
                headers={"Authorization": f"Bearer {self._token}"},
                data={"users": user_id}
            )
            return response.json()


class SlackWebhook:
    """Slack webhook for simple messaging."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(
        self,
        text: str,
        blocks: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> bool:
        """Send message via webhook."""
        if not httpx:
            return False
        
        data = {"text": text}
        if blocks:
            data["blocks"] = blocks
        if attachments:
            data["attachments"] = attachments
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=data)
                return response.status_code == 200
        except:
            return False


__all__ = ["SlackClient", "SlackWebhook", "SlackConfig"]
