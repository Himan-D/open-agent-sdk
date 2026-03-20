"""Gateway - Central routing and session management for OpenAgent.

Inspired by OpenClaw's Gateway architecture:
- Channel adapters for multi-platform support
- Session management with persistent state
- Agent registry and routing
- WebSocket/HTTP endpoints for external access
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import structlog

from open_agent.orchestration.openclaw import DeepAgent, AgentContext, Message

logger = structlog.get_logger(__name__)


class Channel(str, Enum):
    """Supported communication channels."""
    TERMINAL = "terminal"
    HTTP = "http"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"


@dataclass
class Binding:
    """Message routing binding."""
    channel: Channel
    account_id: str
    agent_id: str
    priority: int = 0


@dataclass
class Session:
    """An active conversation session."""
    session_id: str
    agent_id: str
    user_id: Optional[str] = None
    channel: Optional[Channel] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_count: int = 0


class Gateway:
    """Central gateway for message routing and agent orchestration.

    Key features:
    - Multi-agent support with agent registry
    - Session management with context persistence
    - Channel adapters for various platforms
    - Binding-based message routing
    """

    def __init__(
        self,
        name: str = "open-agent-gateway",
        enable_http: bool = False,
        enable_websocket: bool = False,
        port: int = 8080,
    ):
        self.name = name
        self.port = port
        self.enable_http = enable_http
        self.enable_websocket = enable_websocket

        self._agents: Dict[str, DeepAgent] = {}
        self._sessions: Dict[str, Session] = {}
        self._bindings: List[Binding] = []
        self._http_server = None
        self._ws_server = None

        logger.info("gateway_initialized", name=name, port=port)

    def register_agent(self, agent: DeepAgent) -> None:
        """Register an agent with the gateway."""
        self._agents[agent.name] = agent
        logger.info("agent_registered", agent_name=agent.name, agent_id=agent.name)

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("agent_unregistered", agent_id=agent_id)
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[DeepAgent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents."""
        return [{"id": name, "name": agent.name} for name, agent in self._agents.items()]

    def add_binding(self, binding: Binding) -> None:
        """Add a routing binding."""
        self._bindings.append(binding)
        self._bindings.sort(key=lambda b: b.priority, reverse=True)
        logger.info("binding_added", channel=binding.channel, agent_id=binding.agent_id)

    def route_message(self, channel: str, account_id: str) -> Optional[str]:
        """Route a message to the appropriate agent based on bindings."""
        for binding in self._bindings:
            if binding.channel == channel and binding.account_id == account_id:
                return binding.agent_id
        # Fallback to first registered agent
        if self._agents:
            return list(self._agents.keys())[0]
        return None

    async def create_session(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        channel: Optional[Channel] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Create a new session."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")

        session_id = f"session_{int(time.time() * 1000)}"
        session = Session(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            channel=channel,
            metadata=metadata or {},
        )
        self._sessions[session_id] = session
        await self._agents[agent_id].initialize()

        logger.info("session_created", session_id=session_id, agent_id=agent_id)
        return session

    async def process_message(
        self,
        session_id: str,
        content: str,
    ) -> str:
        """Process a message in a session."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        agent = self._agents.get(session.agent_id)
        if not agent:
            raise ValueError(f"Agent '{session.agent_id}' not found")

        context = AgentContext(
            session_id=session_id,
            user_id=session.user_id,
            channel=session.channel.value if session.channel else None,
        )

        session.last_activity = time.time()
        session.message_count += 1

        logger.debug("processing_message", session_id=session_id, message_length=len(content))

        response = await agent.process_message(content, context)

        session.last_activity = time.time()
        return response

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[Session]:
        """List all active sessions."""
        return list(self._sessions.values())

    async def close_session(self, session_id: str) -> bool:
        """Close a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("session_closed", session_id=session_id)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "agent_count": len(self._agents),
            "session_count": len(self._sessions),
            "binding_count": len(self._bindings),
            "total_messages": sum(s.message_count for s in self._sessions.values()),
        }

    async def start(self) -> None:
        """Start the gateway servers."""
        if self.enable_http:
            await self._start_http_server()

        if self.enable_websocket:
            await self._start_websocket_server()

        logger.info("gateway_started", port=self.port)

    async def stop(self) -> None:
        """Stop the gateway servers."""
        if self._http_server:
            self._http_server.close()
        if self._ws_server:
            self._ws_server.close()
        logger.info("gateway_stopped")

    async def _start_http_server(self) -> None:
        """Start HTTP server for REST API."""
        try:
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            import uvicorn

            app = FastAPI(title="OpenAgent Gateway")

            @app.get("/health")
            async def health():
                return {"status": "healthy", "gateway": self.name}

            @app.get("/agents")
            async def list_agents():
                return {"agents": self.list_agents()}

            @app.get("/sessions")
            async def list_sessions():
                return {"sessions": [s.session_id for s in self.list_sessions()]}

            @app.post("/sessions")
            async def create_session_endpoint(request: Dict[str, Any]):
                session = await self.create_session(
                    agent_id=request.get("agent_id", "default"),
                    user_id=request.get("user_id"),
                )
                return {"session_id": session.session_id}

            @app.get("/sessions/{session_id}")
            async def get_session_endpoint(session_id: str):
                session = self.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                return session.__dict__

            @app.post("/sessions/{session_id}/messages")
            async def send_message(session_id: str, request: Dict[str, Any]):
                content = request.get("content", "")
                response = await self.process_message(session_id, content)
                return {"response": response}

            @app.get("/stats")
            async def stats():
                return self.get_stats()

            self._http_server = uvicorn.Server(
                uvicorn.Config(app, host="0.0.0.0", port=self.port)
            )
            await self._http_server.serve()

        except ImportError:
            logger.warning("fastapi_not_available", message="Install fastapi and uvicorn for HTTP API")

    async def _start_websocket_server(self) -> None:
        """Start WebSocket server for real-time communication."""
        try:
            import websockets

            clients: Dict[str, Any] = {}

            async def handle_client(websocket, path):
                client_id = str(id(websocket))
                clients[client_id] = websocket
                logger.info("ws_client_connected", client_id=client_id)

                try:
                    async for message in websocket:
                        import json
                        data = json.loads(message)

                        if data.get("type") == "create_session":
                            session = await self.create_session(
                                agent_id=data.get("agent_id", "default"),
                                user_id=data.get("user_id"),
                            )
                            await websocket.send(json.dumps({
                                "type": "session_created",
                                "session_id": session.session_id,
                            }))

                        elif data.get("type") == "message":
                            session_id = data.get("session_id")
                            content = data.get("content", "")
                            response = await self.process_message(session_id, content)
                            await websocket.send(json.dumps({
                                "type": "response",
                                "content": response,
                            }))

                except Exception as e:
                    logger.error("ws_client_error", client_id=client_id, error=str(e))
                finally:
                    del clients[client_id]
                    logger.info("ws_client_disconnected", client_id=client_id)

            self._ws_server = await websockets.serve(
                handle_client,
                "0.0.0.0",
                self.port + 1,
            )

        except ImportError:
            logger.warning("websockets_not_available", message="Install websockets for WebSocket support")


def create_gateway(
    name: str = "open-agent-gateway",
    port: int = 8080,
    enable_http: bool = True,
    enable_websocket: bool = True,
) -> Gateway:
    """Create a configured gateway instance."""
    return Gateway(
        name=name,
        port=port,
        enable_http=enable_http,
        enable_websocket=enable_websocket,
    )
