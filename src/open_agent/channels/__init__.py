"""Channels module - Multi-platform channel integrations."""

from open_agent.channels.registry import ChannelRegistry, Channel
from open_agent.channels.transport.base import Transport, TransportConfig

__all__ = [
    "ChannelRegistry",
    "Channel",
    "Transport",
    "TransportConfig",
]
