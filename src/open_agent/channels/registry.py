"""Channel registry - Manages available channels."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Channel:
    """A communication channel."""
    name: str
    description: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None
    handler: Optional[Callable] = None


class ChannelRegistry:
    """Registry for managing communication channels.
    
    Similar to OpenClaw's channel registry for managing
    integrations with various messaging platforms.
    """

    def __init__(self):
        self.channels: Dict[str, Channel] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a channel."""
        self.channels[name] = Channel(
            name=name,
            description=description,
            handler=handler,
            config=config,
        )
        logger.info("channel_registered", name=name)

    def unregister(self, name: str) -> bool:
        """Unregister a channel."""
        if name in self.channels:
            del self.channels[name]
            logger.info("channel_unregistered", name=name)
            return True
        return False

    def get(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        return self.channels.get(name)

    def list(self, enabled_only: bool = True) -> List[Channel]:
        """List all channels."""
        channels = list(self.channels.values())
        if enabled_only:
            channels = [c for c in channels if c.enabled]
        return channels

    def enable(self, name: str) -> bool:
        """Enable a channel."""
        channel = self.channels.get(name)
        if channel:
            channel.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a channel."""
        channel = self.channels.get(name)
        if channel:
            channel.enabled = False
            return True
        return False
