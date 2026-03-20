"""Base transport classes for channel communication."""

from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
import asyncio
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class TransportConfig:
    """Configuration for a transport."""
    name: str
    host: str = "0.0.0.0"
    port: int = 8080
    ssl_enabled: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    max_connections: int = 1000
    timeout: int = 30
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Transport:
    """Base class for transport implementations.
    
    Similar to OpenClaw's transport layer for handling
    incoming and outgoing communications.
    """

    def __init__(self, config: TransportConfig):
        self.config = config
        self._running = False
        self._handlers: Dict[str, Callable] = {}

    async def start(self) -> None:
        """Start the transport."""
        if self._running:
            return
        self._running = True
        logger.info("transport_started", name=self.config.name)

    async def stop(self) -> None:
        """Stop the transport."""
        if not self._running:
            return
        self._running = False
        logger.info("transport_stopped", name=self.config.name)

    def register_handler(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        self._handlers[event] = handler

    async def send(self, target: str, message: Any) -> bool:
        """Send a message to a target."""
        raise NotImplementedError

    async def broadcast(self, message: Any) -> None:
        """Broadcast a message to all connected clients."""
        raise NotImplementedError

    @property
    def is_running(self) -> bool:
        """Check if transport is running."""
        return self._running
