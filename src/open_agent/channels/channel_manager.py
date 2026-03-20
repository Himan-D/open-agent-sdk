"""Channels system - Multi-platform message integrations.

Supports:
- Slack
- Discord
- Telegram
- WhatsApp
- WebSocket
- HTTP Webhook
"""

from typing import Optional, Dict, List, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class ChannelType(str, Enum):
    """Supported channel types."""
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEBSOCKET = "websocket"
    HTTP = "http"


@dataclass
class ChannelConfig:
    """Configuration for a channel."""
    channel_type: ChannelType
    enabled: bool = True
    bot_token: Optional[str] = None
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    chat_id: Optional[str] = None
    workspace_id: Optional[str] = None
    channel_id: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """A message from a channel."""
    content: str
    channel: ChannelType
    sender_id: str
    sender_name: str
    channel_id: str
    timestamp: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseChannel(ABC):
    """Base class for channel adapters."""

    def __init__(self, config: ChannelConfig):
        self.config = config
        self._message_handlers: List[Callable] = []
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the channel."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the channel."""
        pass

    @abstractmethod
    async def send_message(self, content: str, channel_id: Optional[str] = None) -> bool:
        """Send a message to the channel."""
        pass

    async def on_message(self, handler: Callable) -> None:
        """Register a message handler."""
        self._message_handlers.append(handler)

    async def _handle_incoming(self, message: Message) -> None:
        """Handle an incoming message."""
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error("message_handler_error", error=str(e))

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected


class SlackChannel(BaseChannel):
    """Slack channel integration."""

    async def connect(self) -> bool:
        """Connect to Slack."""
        if not self.config.bot_token:
            logger.error("slack_no_token")
            return False

        try:
            from slack_sdk import WebClient

            self._client = WebClient(token=self.config.bot_token)
            self._connected = True
            logger.info("slack_connected")
            return True
        except ImportError:
            logger.error("slack_sdk_not_installed")
            return False
        except Exception as e:
            logger.error("slack_connect_error", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from Slack."""
        self._connected = False
        logger.info("slack_disconnected")

    async def send_message(self, content: str, channel_id: Optional[str] = None) -> bool:
        """Send a message to Slack."""
        if not self._connected:
            return False

        target = channel_id or self.config.channel_id
        if not target:
            return False

        try:
            self._client.chat_postMessage(channel=target, text=content)
            return True
        except Exception as e:
            logger.error("slack_send_error", error=str(e))
            return False

    async def start_listening(self) -> None:
        """Start listening for messages."""
        from slack_sdk.socket_mode import SocketModeClient

        if not self._connected:
            return

        self._socket = SocketModeClient(
            app_token=self.config.api_key,
            web_client=self._client,
        )

        @self._socket.socket_mode_request_listeners.append
        def handle(client, req):
            if req.type == "events_api":
                self._handle_incoming(Message(
                    content=req.payload.get("event", {}).get("text", ""),
                    channel=ChannelType.SLACK,
                    sender_id=req.payload.get("event", {}).get("user", ""),
                    sender_name="Unknown",
                    channel_id=req.payload.get("event", {}).get("channel", ""),
                ))


class DiscordChannel(BaseChannel):
    """Discord channel integration."""

    async def connect(self) -> bool:
        """Connect to Discord."""
        if not self.config.bot_token:
            logger.error("discord_no_token")
            return False

        try:
            import discord

            intents = discord.Intents.default()
            intents.message_content = True
            self._client = discord.Client(intents=intents)
            self._connected = True
            logger.info("discord_connected")
            return True
        except ImportError:
            logger.error("discord_py_not_installed")
            return False
        except Exception as e:
            logger.error("discord_connect_error", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from Discord."""
        if hasattr(self, "_client"):
            await self._client.close()
        self._connected = False

    async def send_message(self, content: str, channel_id: Optional[str] = None) -> bool:
        """Send a message to Discord."""
        if not self._connected:
            return False

        target = channel_id or self.config.channel_id
        if not target:
            return False

        try:
            channel = self._client.get_channel(int(target))
            if channel:
                await channel.send(content)
                return True
        except Exception as e:
            logger.error("discord_send_error", error=str(e))
        return False


class TelegramChannel(BaseChannel):
    """Telegram channel integration."""

    async def connect(self) -> bool:
        """Connect to Telegram."""
        if not self.config.bot_token:
            logger.error("telegram_no_token")
            return False

        try:
            import telegram

            self._bot = telegram.Bot(token=self.config.bot_token)
            self._connected = True
            logger.info("telegram_connected")
            return True
        except ImportError:
            logger.error("python-telegram-bot_not_installed")
            return False
        except Exception as e:
            logger.error("telegram_connect_error", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if hasattr(self, "_bot"):
            await self._bot.close()
        self._connected = False

    async def send_message(self, content: str, chat_id: Optional[str] = None) -> bool:
        """Send a message to Telegram."""
        if not self._connected:
            return False

        target = chat_id or self.config.chat_id
        if not target:
            return False

        try:
            await self._bot.send_message(chat_id=target, text=content)
            return True
        except Exception as e:
            logger.error("telegram_send_error", error=str(e))
            return False


class WebSocketChannel(BaseChannel):
    """WebSocket channel for browser/app clients."""

    def __init__(self, config: ChannelConfig):
        super().__init__(config)
        self._clients: Dict[str, Any] = {}
        self._server = None

    async def connect(self) -> bool:
        """Start WebSocket server."""
        try:
            import websockets

            async def handle_client(websocket, path):
                client_id = str(id(websocket))
                self._clients[client_id] = websocket

                async for message in websocket:
                    await self._handle_incoming(Message(
                        content=message,
                        channel=ChannelType.WEBSOCKET,
                        sender_id=client_id,
                        sender_name="WebSocket Client",
                        channel_id=client_id,
                    ))

            port = self.config.custom_settings.get("port", 8765)
            self._server = await websockets.serve(handle_client, "0.0.0.0", port)
            self._connected = True
            logger.info("websocket_server_started", port=port)
            return True
        except Exception as e:
            logger.error("websocket_connect_error", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Stop WebSocket server."""
        if self._server:
            self._server.close()
        self._connected = False

    async def send_message(self, content: str, client_id: Optional[str] = None) -> bool:
        """Send message to WebSocket clients."""
        if not self._clients:
            return False

        try:
            if client_id:
                websocket = self._clients.get(client_id)
                if websocket:
                    await websocket.send(content)
            else:
                for websocket in self._clients.values():
                    await websocket.send(content)
            return True
        except Exception as e:
            logger.error("websocket_send_error", error=str(e))
            return False


class ChannelManager:
    """Manager for all channel integrations."""

    def __init__(self):
        self._channels: Dict[ChannelType, BaseChannel] = {}
        self._gateways: Dict[str, Any] = {}

    def add_channel(self, channel_type: ChannelType, config: ChannelConfig) -> BaseChannel:
        """Add and configure a channel."""
        if channel_type == ChannelType.SLACK:
            channel = SlackChannel(config)
        elif channel_type == ChannelType.DISCORD:
            channel = DiscordChannel(config)
        elif channel_type == ChannelType.TELEGRAM:
            channel = TelegramChannel(config)
        elif channel_type == ChannelType.WEBSOCKET:
            channel = WebSocketChannel(config)
        else:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        self._channels[channel_type] = channel
        return channel

    def get_channel(self, channel_type: ChannelType) -> Optional[BaseChannel]:
        """Get a channel by type."""
        return self._channels.get(channel_type)

    def list_channels(self) -> List[Dict[str, Any]]:
        """List all configured channels."""
        return [
            {
                "type": ch.config.channel_type.value,
                "enabled": ch.config.enabled,
                "connected": ch.is_connected,
            }
            for ch in self._channels.values()
        ]

    async def connect_all(self) -> Dict[str, bool]:
        """Connect all channels."""
        results = {}
        for channel_type, channel in self._channels.items():
            if channel.config.enabled:
                results[channel_type.value] = await channel.connect()
        return results

    async def disconnect_all(self) -> None:
        """Disconnect all channels."""
        for channel in self._channels.values():
            await channel.disconnect()

    def register_message_handler(self, handler: Callable) -> None:
        """Register a global message handler."""
        for channel in self._channels.values():
            channel.on_message(handler)


def create_channel_manager() -> ChannelManager:
    """Create a channel manager."""
    return ChannelManager()
