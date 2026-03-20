"""Plugin manager - Plugin system for extensibility."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Plugin:
    """A plugin definition."""
    name: str
    version: str
    description: str
    author: str = ""
    enabled: bool = True
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class PluginManager:
    """Manages plugins for the agent platform.
    
    Similar to OpenClaw's plugin system for extending
    functionality through external modules.
    """

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin."""
        self.plugins[plugin.name] = plugin
        logger.info("plugin_registered", name=plugin.name, version=plugin.version)

    def unregister_plugin(self, name: str) -> bool:
        """Unregister a plugin."""
        if name in self.plugins:
            del self.plugins[name]
            logger.info("plugin_unregistered", name=name)
            return True
        return False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list_plugins(self, enabled_only: bool = True) -> List[Plugin]:
        """List all plugins."""
        plugins = list(self.plugins.values())
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        return plugins

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = True
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = False
            return True
        return False

    def register_hook(self, event: str, handler: Callable) -> None:
        """Register a hook handler."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    async def trigger_hook(self, event: str, *args, **kwargs) -> List[Any]:
        """Trigger all handlers for an event."""
        results = []
        for handler in self._hooks.get(event, []):
            try:
                result = handler(*args, **kwargs)
                if hasattr(result, "__await__"):
                    result = await result
                results.append(result)
            except Exception as e:
                logger.error("hook_handler_error", event=event, error=str(e))
        return results
