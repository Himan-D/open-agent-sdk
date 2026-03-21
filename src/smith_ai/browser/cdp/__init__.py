"""Chrome DevTools Protocol - Low-level browser control.

This module provides direct CDP access for:
- Browser debugging
- Network interception
- Performance monitoring
- DOM manipulation
- Mobile emulation
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid


class CDP_DOMAIN(Enum):
    """CDP domains."""
    PAGE = "Page"
    NETWORK = "Network"
    DOM = "DOM"
    Runtime = "Runtime"
    LOG = "Log"
    PERFORMANCE = "Performance"
    STORAGE = "Storage"
    TARGET = "Target"
    FETCH = "Fetch"
    SECURITY = "Security"
    AUDIT = "Audits"
    CSS = "CSS"
    SCREENSHOT = "Page"


@dataclass
class CDPMessage:
    """CDP protocol message."""
    id: int
    method: str
    params: Dict[str, Any] = None
    result: Any = None
    error: Any = None


class CDPClient:
    """Chrome DevTools Protocol client.
    
    Provides low-level access to browser internals for:
    - Network request/response inspection
    - JavaScript execution
    - DOM manipulation
    - Performance profiling
    - Security auditing
    """
    
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self._ws = None
        self._message_id = 0
        self._callbacks: Dict[int, asyncio.Future] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> None:
        """Connect to CDP websocket."""
        import websockets
        
        self._ws = await websockets.connect(self.websocket_url)
        asyncio.create_task(self._receive_loop())
    
    async def _receive_loop(self) -> None:
        """Receive messages from CDP."""
        async for message in self._ws:
            data = json.loads(message)
            
            if "id" in data:
                callback = self._callbacks.pop(data["id"], None)
                if callback:
                    if "result" in data:
                        callback.set_result(data["result"])
                    elif "error" in data:
                        callback.set_exception(Exception(data["error"]))
            
            elif "method" in data:
                await self._dispatch_event(data["method"], data.get("params", {}))
    
    async def _dispatch_event(self, method: str, params: Dict) -> None:
        """Dispatch event to handlers."""
        handlers = self._event_handlers.get(method, [])
        for handler in handlers:
            asyncio.create_task(handler(params))
    
    async def send(self, method: str, params: Optional[Dict] = None) -> Any:
        """Send CDP command and wait for response."""
        if not self._ws:
            raise RuntimeError("Not connected")
        
        msg_id = self._message_id
        self._message_id += 1
        
        message = {"id": msg_id, "method": method}
        if params:
            message["params"] = params
        
        future = asyncio.Future()
        self._callbacks[msg_id] = future
        
        await self._ws.send(json.dumps(message))
        return await future
    
    def on(self, event: str, handler: Callable) -> None:
        """Register event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def close(self) -> None:
        """Close connection."""
        if self._ws:
            await self._ws.close()


class CDPBrowser:
    """High-level CDP browser control.
    
    Provides convenient methods for common browser operations
    via Chrome DevTools Protocol.
    """
    
    def __init__(self, cdp: CDPClient):
        self.cdp = cdp
        self._target_id: Optional[str] = None
    
    async def create_page(self) -> str:
        """Create a new page."""
        result = await self.cdp.send("Target.createTarget", {
            "url": "about:blank"
        })
        self._target_id = result["targetId"]
        return self._target_id
    
    async def close_page(self, target_id: str) -> None:
        """Close a page."""
        await self.cdp.send("Target.closeTarget", {
            "targetId": target_id
        })
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        return await self.cdp.send("Page.navigate", {"url": url})
    
    async def reload(self, hard: bool = False) -> None:
        """Reload the page."""
        await self.cdp.send("Page.reload", {"ignoreCache": hard})
    
    async def go_back(self) -> None:
        """Go back in history."""
        await self.cdp.send("Runtime.evaluate", {
            "expression": "history.back()"
        })
    
    async def go_forward(self) -> None:
        """Go forward in history."""
        await self.cdp.send("Runtime.evaluate", {
            "expression": "history.forward()"
        })
    
    async def get_html(self) -> str:
        """Get page HTML."""
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML"
        })
        return result.get("result", {}).get("value", "")
    
    async def get_title(self) -> str:
        """Get page title."""
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": "document.title"
        })
        return result.get("result", {}).get("value", "")
    
    async def click(self, selector: str) -> None:
        """Click element by selector."""
        await self.cdp.send("Runtime.evaluate", {
            "expression": f"""
                document.querySelector('{selector}').click()
            """
        })
    
    async def fill(self, selector: str, value: str) -> None:
        """Fill input by selector."""
        escaped_value = value.replace("'", "\\'")
        await self.cdp.send("Runtime.evaluate", {
            "expression": f"""
                document.querySelector('{selector}').value = '{escaped_value}';
            """
        })
    
    async def submit(self, selector: str) -> None:
        """Submit form by selector."""
        await self.cdp.send("Runtime.evaluate", {
            "expression": f"""
                document.querySelector('{selector}').submit()
            """
        })
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript."""
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": script
        })
        return result.get("result", {}).get("value")
    
    async def screenshot(self, full_page: bool = False) -> bytes:
        """Take screenshot."""
        result = await self.cdp.send("Page.captureScreenshot", {
            "format": "png",
            "fullPage": full_page
        })
        import base64
        return base64.b64decode(result["data"])
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies."""
        result = await self.cdp.send("Network.getAllCookies")
        return result.get("cookies", [])
    
    async def set_cookie(self, name: str, value: str, domain: str = "") -> None:
        """Set a cookie."""
        await self.cdp.send("Network.setCookie", {
            "name": name,
            "value": value,
            "domain": domain,
        })
    
    async def delete_cookies(self, name: str, domain: str = "") -> None:
        """Delete a cookie."""
        await self.cdp.send("Network.deleteCookies", {
            "name": name,
            "domain": domain,
        })
    
    async def clear_cache(self) -> None:
        """Clear browser cache."""
        await self.cdp.send("Network.clearBrowserCache")
    
    async def clear_cookies(self) -> None:
        """Clear all cookies."""
        await self.cdp.send("Network.clearBrowserCookies")
    
    async def set_viewport(
        self,
        width: int,
        height: int,
        device_scale_factor: float = 1.0
    ) -> None:
        """Set viewport size."""
        await self.cdp.send("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": device_scale_factor,
            "mobile": width < 768
        })
    
    async def set_user_agent(self, user_agent: str) -> None:
        """Set custom user agent."""
        await self.cdp.send("Network.setUserAgentOverride", {
            "userAgent": user_agent
        })
    
    async def enable_network_logging(self) -> None:
        """Enable network request logging."""
        await self.cdp.send("Network.enable")
        await self.cdp.send("Log.enable")
    
    def on_network_request(self, handler: Callable[[Dict], None]) -> None:
        """Register network request handler."""
        self.cdp.on("Network.requestWillBeSent", handler)
    
    def on_network_response(self, handler: Callable[[Dict], None]) -> None:
        """Register network response handler."""
        self.cdp.on("Network.responseReceived", handler)


class NetworkInterceptor:
    """Intercept and modify network requests."""
    
    def __init__(self, cdp: CDPClient):
        self.cdp = cdp
        self._blocked_patterns: List[str] = []
        self._mocked_responses: Dict[str, Dict] = {}
    
    async def enable(self) -> None:
        """Enable request interception."""
        patterns = [{"urlPattern": "*", "resourceType": "*", "interceptionStage": "HeadersReceived"}]
        await self.cdp.send("Fetch.enable", {"patterns": patterns})
        
        asyncio.create_task(self._interception_loop())
    
    async def _interception_loop(self) -> None:
        """Handle intercepted requests."""
        async for message in self.cdp._ws:
            data = json.loads(message)
            if data.get("method") == "Fetch.requestPaused":
                await self._handle_paused_request(data["params"])
    
    async def _handle_paused_request(self, params: Dict) -> None:
        """Handle paused request."""
        request_id = params["requestId"]
        url = params["request"]["url"]
        
        if url in self._mocked_responses:
            response = self._mocked_responses[url]
            await self.cdp.send("Fetch.fulfillRequest", {
                "requestId": request_id,
                "responseCode": response.get("status", 200),
                "responseHeaders": response.get("headers", {}),
                "body": response.get("body", ""),
            })
        else:
            await self.cdp.send("Fetch.continueRequest", {
                "requestId": request_id
            })
    
    def mock_response(self, url: str, response: Dict) -> None:
        """Mock a response for URL."""
        self._mocked_responses[url] = response
    
    def block_pattern(self, pattern: str) -> None:
        """Block URLs matching pattern."""
        self._blocked_patterns.append(pattern)


__all__ = [
    "CDPClient",
    "CDPBrowser",
    "NetworkInterceptor",
    "CDP_DOMAIN",
    "CDPMessage",
]
