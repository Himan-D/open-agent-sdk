"""Session manager - Manages agent sessions and conversation history."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Session:
    """An agent session."""
    session_id: str
    user_id: Optional[str] = None
    channel: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        self.message_count += 1


class SessionManager:
    """Manages agent sessions and conversation history.
    
    Similar to OpenClaw's sessions system for managing
    conversation contexts across channels.
    """

    def __init__(self, max_sessions: int = 1000, session_timeout: int = 3600):
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._cleanup_task: Optional[asyncio.Task] = None

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Create a new session."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        if len(self.sessions) >= self.max_sessions:
            await self._cleanup_old_sessions()

        session = Session(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            metadata=metadata or {},
        )
        self.sessions[session_id] = session
        logger.info("session_created", session_id=session_id)
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[Session]:
        """List sessions, optionally filtered."""
        sessions = list(self.sessions.values())
        
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        if channel:
            sessions = [s for s in sessions if s.channel == channel]
        
        return sessions

    async def _cleanup_old_sessions(self) -> None:
        """Clean up old sessions."""
        now = datetime.now()
        old_sessions = [
            sid for sid, session in self.sessions.items()
            if (now - session.last_activity).total_seconds() > self.session_timeout
        ]
        
        for session_id in old_sessions:
            await self.delete_session(session_id)
        
        if old_sessions:
            logger.info("sessions_cleaned", count=len(old_sessions))

    async def start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task is not None:
            return

        async def cleanup_loop():
            while True:
                await asyncio.sleep(300)
                await self._cleanup_old_sessions()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop the periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
