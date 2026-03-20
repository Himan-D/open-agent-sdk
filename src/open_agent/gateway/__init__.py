"""Gateway module - Message routing and session management.

This module provides the gateway system similar to OpenClaw:
- Protocol handling for agent communication
- Session management
- Authentication and authorization
- Message routing
"""

from open_agent.gateway.protocol.router import MessageRouter
from open_agent.gateway.sessions.manager import SessionManager
from open_agent.gateway.auth.auth import AuthHandler

__all__ = [
    "MessageRouter",
    "SessionManager",
    "AuthHandler",
]
