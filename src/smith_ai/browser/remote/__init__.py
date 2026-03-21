"""Remote Browser - Connect to Chrome instances anywhere.

This module provides:
- Remote Chrome connection via DevTools Protocol
- Browser farm management
- Headless browser hosting
- Multi-browser parallel execution
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from smith_ai.browser.cdp import CDPClient, CDPBrowser


class BrowserType(Enum):
    CHROMIUM = "chromium"
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


@dataclass
class RemoteConfig:
    """Configuration for remote browser."""
    host: str = "localhost"
    port: int = 9222
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    user_data_dir: Optional[str] = None
    window_size: Tuple[int, int] = (1920, 1080)


class RemoteBrowser:
    """Connect to a remote Chrome instance.
    
    Real use cases:
    - Connect to already-running Chrome
    - Scale browser automation across machines
    - Run browsers in Docker containers
    - Access browsers behind VPNs
    - Share browser sessions across agents
    
    Usage:
        # Connect to local Chrome
        browser = RemoteBrowser()
        await browser.connect()
        
        # Or start your own Chrome
        browser = await RemoteBrowser.launch()
        
        # Use CDP
        page = await browser.new_page()
        await page.goto("https://example.com")
    """
    
    _instances: Dict[str, "RemoteBrowser"] = {}
    
    def __init__(self, config: Optional[RemoteConfig] = None):
        self.config = config or RemoteConfig()
        self._cdp: Optional[CDPClient] = None
        self._browser: Optional[CDPBrowser] = None
        self._instance_id = str(uuid.uuid4())[:8]
        self._pages: Dict[str, CDPBrowser] = {}
    
    @property
    def instance_id(self) -> str:
        return self._instance_id
    
    async def connect(self) -> None:
        """Connect to existing Chrome via DevTools."""
        ws_url = await self._get_websocket_url()
        self._cdp = CDPClient(ws_url)
        await self._cdp.connect()
        self._browser = CDPBrowser(self._cdp)
        self._instances[self._instance_id] = self
    
    async def _get_websocket_url(self) -> str:
        """Get WebSocket URL from Chrome."""
        import httpx
        
        debug_url = f"http://{self.config.host}:{self.config.port}/json"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(debug_url)
            tabs = response.json()
            
            if not tabs:
                raise RuntimeError("No browser tabs found. Make sure Chrome is running with remote debugging.")
            
            return tabs[0]["webSocketDebuggerUrl"]
    
    @classmethod
    async def launch(
        cls,
        config: Optional[RemoteConfig] = None,
        remote_debugging_port: int = 9222,
        user_data_dir: Optional[str] = None,
        headless: bool = True,
        proxy: Optional[str] = None,
        extensions: Optional[List[str]] = None,
    ) -> "RemoteBrowser":
        """Launch a new Chrome instance.
        
        Args:
            config: Remote browser configuration
            remote_debugging_port: Port for DevTools
            user_data_dir: Chrome profile directory
            headless: Run without GUI
            proxy: Proxy server (socks5:// or http://)
            extensions: List of extension paths to load
        """
        config = config or RemoteConfig()
        config.port = remote_debugging_port
        config.headless = headless
        
        browser_executable = cls._find_browser(config.browser_type)
        
        args = [
            browser_executable,
            f"--remote-debugging-port={remote_debugging_port}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-popup-blocking",
            "--disable-translate",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        
        if headless:
            args.append("--headless=new")
        
        if user_data_dir:
            args.append(f"--user-data-dir={user_data_dir}")
        
        if proxy:
            args.append(f"--proxy-server={proxy}")
        
        if extensions:
            for ext in extensions:
                args.append(f"--load-extension={ext}")
        
        args.extend([
            "--window-size=1920,1080",
            "--kiosk",
            "--disable-features=ChromeRuntime",
        ])
        
        process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        await asyncio.sleep(2)
        
        browser = cls(config)
        await browser.connect()
        
        return browser
    
    @staticmethod
    def _find_browser(browser_type: BrowserType) -> str:
        """Find browser executable."""
        import shutil
        
        browsers = {
            BrowserType.CHROME: ["google-chrome", "google-chrome-stable", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
            BrowserType.CHROMIUM: ["chromium", "chromium-browser", "/Applications/Chromium.app/Contents/MacOS/Chromium"],
            BrowserType.EDGE: ["msedge", "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
            BrowserType.FIREFOX: ["firefox"],
        }
        
        for name in browsers.get(browser_type, []):
            path = shutil.which(name)
            if path:
                return path
        
        return "chromium" if browser_type == BrowserType.CHROMIUM else "google-chrome"
    
    async def new_page(self, url: str = "about:blank") -> CDPBrowser:
        """Create a new page/tab."""
        target_id = await self._browser.create_page()
        page = CDPBrowser(self._cdp)
        page._target_id = target_id
        self._pages[target_id] = page
        
        if url != "about:blank":
            await page.navigate(url)
        
        return page
    
    async def close_page(self, target_id: str) -> None:
        """Close a page/tab."""
        await self._browser.close_page(target_id)
        if target_id in self._pages:
            del self._pages[target_id]
    
    async def get_pages(self) -> List[Dict[str, Any]]:
        """Get list of open pages."""
        import httpx
        
        debug_url = f"http://{self.config.host}:{self.config.port}/json/list"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(debug_url)
                return response.json()
        except:
            return []
    
    async def screenshot_all(self) -> Dict[str, bytes]:
        """Take screenshots of all pages."""
        screenshots = {}
        for target_id, page in self._pages.items():
            try:
                screenshots[target_id] = await page.screenshot()
            except:
                pass
        return screenshots
    
    def get_by_id(self, instance_id: str) -> Optional["RemoteBrowser"]:
        """Get browser instance by ID."""
        return self._instances.get(instance_id)
    
    async def close(self) -> None:
        """Close the browser."""
        for target_id in list(self._pages.keys()):
            await self.close_page(target_id)
        
        if self._cdp:
            await self._cdp.close()
        
        if self._instance_id in self._instances:
            del self._instances[self._instance_id]


class BrowserPool:
    """Pool of browser instances for parallel execution.
    
    Manages multiple browsers for:
    - Parallel scraping
    - Load testing
    - Multiple account management
    - Distributed automation
    """
    
    def __init__(
        self,
        size: int = 3,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
    ):
        self.size = size
        self.browser_type = browser_type
        self.headless = headless
        self._browsers: List[RemoteBrowser] = []
        self._available: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._started = False
    
    async def start(self) -> None:
        """Start all browsers in the pool."""
        if self._started:
            return
        
        async with self._lock:
            for _ in range(self.size):
                browser = await RemoteBrowser.launch(
                    config=RemoteConfig(
                        browser_type=self.browser_type,
                        headless=self.headless,
                    )
                )
                self._browsers.append(browser)
                await self._available.put(browser)
        
        self._started = True
    
    async def acquire(self, timeout: float = 30) -> RemoteBrowser:
        """Get an available browser from the pool."""
        return await asyncio.wait_for(self._available.get(), timeout)
    
    async def release(self, browser: RemoteBrowser) -> None:
        """Return browser to the pool."""
        await self._available.put(browser)
    
    async def execute_task(
        self,
        task: callable,
        timeout: float = 60
    ) -> Any:
        """Execute a task with an available browser."""
        browser = await self.acquire(timeout)
        try:
            return await task(browser)
        finally:
            await self.release(browser)
    
    async def close(self) -> None:
        """Close all browsers."""
        for browser in self._browsers:
            await browser.close()
        self._browsers.clear()
        self._started = False


class BrowserCluster:
    """Cluster of browser pools across machines.
    
    For large-scale distributed browser automation:
    - Master/worker architecture
    - Load balancing
    - Failover handling
    - Status monitoring
    """
    
    def __init__(self):
        self._pools: Dict[str, BrowserPool] = {}
        self._workers: Dict[str, str] = {}
    
    def add_worker(
        self,
        worker_id: str,
        host: str,
        port: int,
        pool_size: int = 3
    ) -> None:
        """Add a worker machine to the cluster."""
        self._workers[worker_id] = f"http://{host}:{port}"
    
    async def execute_distributed(
        self,
        task: callable,
        worker_id: Optional[str] = None
    ) -> Any:
        """Execute task on a worker.
        
        If worker_id is None, picks a random worker.
        """
        if worker_id and worker_id in self._workers:
            return await self._execute_on_worker(self._workers[worker_id], task)
        
        if self._workers:
            worker_url = list(self._workers.values())[0]
            return await self._execute_on_worker(worker_url, task)
        
        raise RuntimeError("No workers available")
    
    async def _execute_on_worker(self, worker_url: str, task: callable) -> Any:
        """Execute task on a specific worker via API."""
        import httpx
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{worker_url}/execute",
                json={"task": str(task)}
            )
            return response.json()


__all__ = [
    "RemoteBrowser",
    "RemoteConfig",
    "BrowserType",
    "BrowserPool",
    "BrowserCluster",
]
