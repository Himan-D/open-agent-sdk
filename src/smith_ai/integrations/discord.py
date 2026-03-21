"""Discord integration for SmithAI.

Provides:
- Webhook messaging
- Embeds
- Channel posting
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class DiscordEmbed:
    title: str = ""
    description: str = ""
    color: int = 0x3498db
    url: str = ""
    author_name: str = ""
    author_url: str = ""
    thumbnail_url: str = ""
    image_url: str = ""
    footer_text: str = ""
    fields: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
    
    def to_dict(self) -> Dict[str, Any]:
        embed = {
            "title": self.title,
            "description": self.description,
            "color": self.color,
        }
        if self.url:
            embed["url"] = self.url
        if self.author_name:
            embed["author"] = {"name": self.author_name, "url": self.author_url}
        if self.thumbnail_url:
            embed["thumbnail"] = {"url": self.thumbnail_url}
        if self.image_url:
            embed["image"] = {"url": self.image_url}
        if self.footer_text:
            embed["footer"] = {"text": self.footer_text}
        if self.fields:
            embed["fields"] = self.fields
        return embed


class DiscordWebhook:
    """Discord webhook client.
    
    Real use cases:
    - Send alerts and notifications
    - Post status updates
    - Share reports
    - Team notifications
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(
        self,
        content: str = "",
        embeds: Optional[List[DiscordEmbed]] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> bool:
        """Send message to Discord channel."""
        if not httpx:
            return False
        
        data = {}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = [e.to_dict() for e in embeds]
        if username:
            data["username"] = username
        if avatar_url:
            data["avatar_url"] = avatar_url
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=data)
                return response.status_code == 204
        except:
            return False
    
    async def send_embed(self, embed: DiscordEmbed) -> bool:
        """Send a single embed."""
        return await self.send(embeds=[embed])
    
    async def send_file(
        self,
        file_path: str,
        content: str = "",
    ) -> bool:
        """Send a file attachment."""
        if not httpx:
            return False
        
        try:
            with open(file_path, "rb") as f:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.webhook_url,
                        data={"content": content},
                        files={"file": f}
                    )
                    return response.status_code == 204
        except:
            return False


class DiscordBot:
    """Discord bot client using discord.py-like interface."""
    
    def __init__(self, token: str):
        self.token = token
        self._guilds: Dict[str, Any] = {}
    
    async def get_guild(self, guild_id: str) -> Dict[str, Any]:
        """Get guild info."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://discord.com/api/v10/guilds/{guild_id}",
                headers={"Authorization": f"Bot {self.token}"}
            )
            return response.json()
    
    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel info."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://discord.com/api/v10/channels/{channel_id}",
                headers={"Authorization": f"Bot {self.token}"}
            )
            return response.json()
    
    async def post_message(
        self,
        channel_id: str,
        content: str,
        embeds: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Post a message to a channel."""
        if not httpx:
            return {}
        
        data = {"content": content}
        if embeds:
            data["embeds"] = embeds
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {self.token}",
                    "Content-Type": "application/json",
                },
                json=data
            )
            return response.json()


__all__ = ["DiscordWebhook", "DiscordBot", "DiscordEmbed"]
