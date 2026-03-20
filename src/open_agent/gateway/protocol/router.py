"""Message router - Routes messages to appropriate agents and sessions."""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
import asyncio
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Route:
    """A message route."""
    name: str
    pattern: str
    handler: Callable
    priority: int = 0


class MessageRouter:
    """Routes messages to appropriate handlers based on patterns.
    
    Similar to OpenClaw's gateway routing system for directing
    messages to appropriate agents and sessions.
    """

    def __init__(self):
        self.routes: Dict[str, Route] = {}
        self.default_handler: Optional[Callable] = None

    def register_route(
        self,
        name: str,
        pattern: str,
        handler: Callable,
        priority: int = 0,
    ) -> None:
        """Register a message route."""
        self.routes[name] = Route(
            name=name,
            pattern=pattern,
            handler=handler,
            priority=priority,
        )
        logger.info("route_registered", name=name, pattern=pattern)

    def register_default(self, handler: Callable) -> None:
        """Register the default message handler."""
        self.default_handler = handler

    async def route(self, message: Any) -> Any:
        """Route a message to the appropriate handler."""
        if not self.routes:
            if self.default_handler:
                result = self.default_handler(message)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            return None

        for route in sorted(self.routes.values(), key=lambda r: -r.priority):
            if self._match_pattern(route.pattern, message):
                try:
                    result = route.handler(message)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return result
                except Exception as e:
                    logger.error("route_handler_error", route=route.name, error=str(e))
                    return None

        if self.default_handler:
            result = self.default_handler(message)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        return None

    def _match_pattern(self, pattern: str, message: Any) -> bool:
        """Match a message against a pattern."""
        if hasattr(message, "content"):
            content = str(message.content).lower()
            return pattern.lower() in content
        return pattern in str(message)
