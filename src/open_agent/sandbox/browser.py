"""Browser sandbox - Playwright-based browser automation."""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import base64
import structlog

logger = structlog.get_logger(__name__)


class BrowserType(str, Enum):
    """Browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserAction(str, Enum):
    """Browser automation actions."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCREENSHOT = "screenshot"
    GET_TEXT = "get_text"
    GET_HTML = "get_html"
    WAIT = "wait"
    SCROLL = "scroll"
    PRESS = "press"
    SELECT = "select"
    HOVER = "hover"


@dataclass
class BrowserConfig:
    """Configuration for browser sandbox."""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    slow_mo: int = 0  # Slow down by ms
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    timeout: int = 30000
    downloads_path: Optional[str] = None


@dataclass
class BrowserResult:
    """Result of a browser action."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    screenshot: Optional[str] = None  # Base64 encoded


class BrowserSandbox:
    """Browser sandbox for web automation.
    
    Similar to OpenClaw's browser sandbox for enabling
    agents to interact with web pages.
    
    Example:
        >>> browser = BrowserSandbox()
        >>> await browser.start()
        >>> result = await browser.navigate("https://example.com")
        >>> screenshot = await browser.screenshot()
        >>> await browser.stop()
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = False

    async def start(self) -> bool:
        """Start the browser."""
        if self._initialized:
            return True

        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            browser_type = self.config.browser_type.value
            
            self._browser = await getattr(self._playwright, browser_type).launch(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo,
            )
            
            context_options = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "timeout": self.config.timeout,
            }
            
            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent
            
            if self.config.proxy:
                context_options["proxy"] = {"server": self.config.proxy}
            
            self._context = await self._browser.new_context(**context_options)
            self._page = await self._context.new_page()
            
            self._initialized = True
            logger.info("browser_started", browser=self.config.browser_type)
            return True
            
        except ImportError:
            logger.warning("playwright_not_installed", message="Install with: pip install playwright")
            return False
        except Exception as e:
            logger.error("browser_start_error", error=str(e))
            return False

    async def stop(self) -> None:
        """Stop the browser."""
        if not self._initialized:
            return

        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            
            self._initialized = False
            logger.info("browser_stopped")
        except Exception as e:
            logger.error("browser_stop_error", error=str(e))

    async def navigate(self, url: str) -> BrowserResult:
        """Navigate to a URL."""
        if not self._initialized:
            success = await self.start()
            if not success:
                return BrowserResult(success=False, error="Failed to start browser")

        try:
            response = await self._page.goto(url, timeout=self.config.timeout)
            
            if response.ok:
                return BrowserResult(
                    success=True,
                    data={"url": self._page.url, "status": response.status},
                )
            else:
                return BrowserResult(
                    success=False,
                    error=f"HTTP {response.status}",
                )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def screenshot(self, full_page: bool = False) -> BrowserResult:
        """Take a screenshot."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            bytes_data = await self._page.screenshot(full_page=full_page)
            base64_data = base64.b64encode(bytes_data).decode()
            
            return BrowserResult(
                success=True,
                data={"format": "png", "size": len(bytes_data)},
                screenshot=base64_data,
            )
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def click(self, selector: str) -> BrowserResult:
        """Click on an element."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.click(selector)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def type_text(self, selector: str, text: str, delay: int = 0) -> BrowserResult:
        """Type text into an element."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.fill(selector, text)
            if delay > 0:
                import asyncio
                await asyncio.sleep(delay / 1000)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_text(self, selector: str) -> BrowserResult:
        """Get text content of an element."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            text = await self._page.text_content(selector)
            return BrowserResult(success=True, data=text)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_html(self) -> BrowserResult:
        """Get the full HTML of the page."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            html = await self._page.content()
            return BrowserResult(success=True, data=html)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> BrowserResult:
        """Wait for an element to appear."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def scroll(self, direction: str = "down", amount: int = 500) -> BrowserResult:
        """Scroll the page."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            if direction == "down":
                await self._page.evaluate(f"window.scrollBy(0, {amount})")
            else:
                await self._page.evaluate(f"window.scrollBy(0, -{amount})")
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def press_key(self, selector: str, key: str) -> BrowserResult:
        """Press a key on an element."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.press(selector, key)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def select_option(self, selector: str, value: str) -> BrowserResult:
        """Select an option in a dropdown."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.select_option(selector, value)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def hover(self, selector: str) -> BrowserResult:
        """Hover over an element."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.hover(selector)
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def execute_script(self, script: str) -> BrowserResult:
        """Execute JavaScript in the page context."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            result = await self._page.evaluate(script)
            return BrowserResult(success=True, data=result)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_title(self) -> BrowserResult:
        """Get the page title."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            title = await self._page.title()
            return BrowserResult(success=True, data=title)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def get_url(self) -> BrowserResult:
        """Get the current URL."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            url = self._page.url
            return BrowserResult(success=True, data=url)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def back(self) -> BrowserResult:
        """Go back in browser history."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.go_back()
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def forward(self) -> BrowserResult:
        """Go forward in browser history."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.go_forward()
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    async def reload(self) -> BrowserResult:
        """Reload the current page."""
        if not self._initialized:
            return BrowserResult(success=False, error="Browser not started")

        try:
            await self._page.reload()
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))

    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._initialized


def create_browser_sandbox(
    browser_type: str = "chromium",
    headless: bool = True,
) -> BrowserSandbox:
    """Create a browser sandbox instance.
    
    Example:
        >>> browser = create_browser_sandbox(browser_type="chromium")
        >>> await browser.start()
    """
    return BrowserSandbox(
        config=BrowserConfig(
            browser_type=BrowserType(browser_type),
            headless=headless,
        )
    )
