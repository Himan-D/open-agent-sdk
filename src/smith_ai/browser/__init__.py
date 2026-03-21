"""Browser automation using Playwright."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from smith_ai.core.types import BaseTool, ToolResult


@dataclass
class BrowserConfig:
    headless: bool = True
    browser_type: str = "chromium"
    viewport: Dict[str, int] = None
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1280, "height": 720}


class BrowserSession:
    """Browser session using Playwright."""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._page = None
        self._context = None
    
    async def initialize(self) -> None:
        """Initialize the browser."""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser_type = getattr(playwright, self.config.browser_type)
            self._browser = await browser_type.launch(headless=self.config.headless)
            self._context = await self._browser.new_context(viewport=self.config.viewport)
            self._page = await self._context.new_page()
        except ImportError:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install")
    
    async def navigate(self, url: str) -> str:
        """Navigate to a URL."""
        if not self._page:
            await self.initialize()
        
        await self._page.goto(url)
        return f"Navigated to {url}"
    
    async def click(self, selector: str) -> str:
        """Click an element."""
        await self._page.click(selector)
        return f"Clicked {selector}"
    
    async def fill(self, selector: str, value: str) -> str:
        """Fill an input field."""
        await self._page.fill(selector, value)
        return f"Filled {selector} with {value}"
    
    async def get_text(self, selector: str) -> str:
        """Get text from an element."""
        return await self._page.text_content(selector) or ""
    
    async def get_html(self) -> str:
        """Get page HTML."""
        return await self._page.content()
    
    async def screenshot(self, path: Optional[str] = None) -> bytes:
        """Take a screenshot."""
        if not path:
            path = "screenshot.png"
        await self._page.screenshot(path=path)
        return path
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript."""
        return await self._page.evaluate(script)
    
    async def close(self) -> None:
        """Close the browser."""
        if self._browser:
            await self._browser.close()


class WebScraper:
    """Web scraper using Playwright."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._session = None
    
    async def _get_session(self) -> BrowserSession:
        if not self._session:
            self._session = BrowserSession(BrowserConfig(headless=self.headless))
            await self._session.initialize()
        return self._session
    
    async def scrape(self, url: str, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Scrape a webpage."""
        session = await self._get_session()
        await session.navigate(url)
        
        result = {
            "url": url,
            "title": await session.get_text("title"),
            "html": await session.get_html(),
        }
        
        if selectors:
            for key, selector in selectors.items():
                try:
                    result[key] = await session.get_text(selector)
                except:
                    result[key] = None
        
        return result
    
    async def close(self) -> None:
        if self._session:
            await self._session.close()


class BrowserTool(BaseTool):
    """Tool for browser automation."""
    
    name = "browser"
    description = "Control a browser (navigate, click, fill, screenshot)"
    category = "automation"
    
    def __init__(self):
        self._session: Optional[BrowserSession] = None
        self._config = BrowserConfig()
    
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute a browser action."""
        try:
            if not self._session:
                self._session = BrowserSession(self._config)
                await self._session.initialize()
            
            actions = {
                "navigate": lambda: self._session.navigate(kwargs.get("url", "")),
                "click": lambda: self._session.click(kwargs.get("selector", "")),
                "fill": lambda: self._session.fill(kwargs.get("selector", ""), kwargs.get("value", "")),
                "screenshot": lambda: self._session.screenshot(kwargs.get("path")),
                "html": lambda: self._session.get_html(),
                "text": lambda: self._session.get_text(kwargs.get("selector", "body")),
            }
            
            if action not in actions:
                return ToolResult(tool_call_id="", success=False, error=f"Unknown action: {action}")
            
            result = await actions[action]()
            return ToolResult(tool_call_id="", success=True, output=str(result))
        
        except ImportError as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))
    
    async def close(self) -> None:
        if self._session:
            await self._session.close()


class WebScraperTool(BaseTool):
    """Tool for web scraping."""
    
    name = "scrape"
    description = "Scrape content from a webpage"
    category = "automation"
    
    def __init__(self):
        self._scraper: Optional[WebScraper] = None
    
    async def execute(self, url: str, selectors: Optional[str] = None) -> ToolResult:
        """Scrape a webpage."""
        try:
            if not self._scraper:
                self._scraper = WebScraper()
            
            selectors_dict = None
            if selectors:
                try:
                    import json
                    selectors_dict = json.loads(selectors)
                except:
                    pass
            
            result = await self._scraper.scrape(url, selectors_dict)
            return ToolResult(tool_call_id="", success=True, output=str(result))
        
        except ImportError as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))
        except Exception as e:
            return ToolResult(tool_call_id="", success=False, error=str(e))


from smith_ai.core.types import BaseTool, ToolResult

__all__ = [
    "BrowserSession",
    "BrowserConfig",
    "WebScraper",
    "BrowserTool",
    "WebScraperTool",
]
