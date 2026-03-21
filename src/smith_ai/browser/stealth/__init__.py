"""Stealth Browser - Anti-detection browser automation.

This module provides browser automation that bypasses:
- Bot detection (Cloudflare, Imperva, etc.)
- Fingerprinting checks
- Canvas/WebGL detection
- Automation markers
- reCaptcha/hCaptcha challenges
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class DetectionLevel(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    MAXIMUM = "maximum"


@dataclass
class StealthConfig:
    """Configuration for stealth browser."""
    level: DetectionLevel = DetectionLevel.STANDARD
    randomize_viewport: bool = True
    randomize_user_agent: bool = True
    block_images: bool = False
    block_css: bool = False
    disable_webdriver: bool = True
    spoof_timezone: bool = True
    spoof_language: bool = True
    spoof_permissions: bool = True
    emulate_device: Optional[str] = None
    proxy: Optional[str] = None


class UserAgentPool:
    """Pool of real user agents to mimic."""
    
    CHROME_WINDOWS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]
    
    CHROME_MAC = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    
    FIREFOX_WINDOWS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    ]
    
    SAFARI_MAC = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    @classmethod
    def get_random(cls, browser: str = "chrome") -> str:
        """Get a random user agent."""
        pools = {
            "chrome": cls.CHROME_WINDOWS + cls.CHROME_MAC,
            "firefox": cls.FIREFOX_WINDOWS,
            "safari": cls.SAFARI_MAC,
        }
        return random.choice(pools.get(browser, cls.CHROME_WINDOWS))


class TimezoneSpoofer:
    """Spoof browser timezone."""
    
    ZONES = [
        "America/New_York",
        "America/Los_Angeles", 
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Australia/Sydney",
    ]
    
    @classmethod
    def get_random(cls) -> str:
        return random.choice(cls.ZONES)


class StealthBrowser:
    """Browser with anti-detection measures.
    
    Real use cases:
    - Web scraping without being blocked
    - Account creation on websites
    - Price monitoring
    - Lead generation
    - Market research
    - Competitor analysis
    """
    
    def __init__(self, config: Optional[StealthConfig] = None):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install")
        
        self.config = config or StealthConfig()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    async def launch(self) -> None:
        """Launch the stealth browser."""
        self._playwright = await async_playwright().start()
        
        browser_type = self._playwright.chromium
        launch_args = self._build_launch_args()
        
        self._browser = await browser_type.launch(
            headless=not self.config.level == DetectionLevel.MAXIMUM,
            args=launch_args,
        )
        
        self._context = await self._browser.new_context(
            **self._build_context_args()
        )
        
        self._page = await self._context.new_page()
        await self._apply_stealth(self._page)
    
    def _build_launch_args(self) -> List[str]:
        """Build Chromium launch arguments for stealth."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--mute-audio",
            "--no-default-browser-check",
            "--disable-features=CookiesWithoutSameSiteMustBeSecure,ImprovedCookieControls,LazyFrameLoading,MediaQuerySet,Prerender2",
        ]
        
        if self.config.level == DetectionLevel.MAXIMUM:
            args.extend([
                "--disable-fingerprinting",
                "--disable-canvas-aa",
                "--disable-webgl",
                "--disable-webgl2",
            ])
        
        if self.config.proxy:
            args.append(f"--proxy-server={self.config.proxy}")
        
        return args
    
    def _build_context_args(self) -> Dict[str, Any]:
        """Build browser context arguments."""
        args = {}
        
        if self.config.emulate_device:
            try:
                device = self._playwright.devices[self.config.emulate_device]
                args.update(device)
            except KeyError:
                pass
        
        if self.config.randomize_viewport:
            width = random.randint(1280, 1920)
            height = random.randint(720, 1080)
            args["viewport"] = {"width": width, "height": height}
        
        if self.config.proxy:
            args["proxy"] = {"server": self.config.proxy}
        
        return args
    
    async def _apply_stealth(self, page: Page) -> None:
        """Apply stealth modifications to the page."""
        await page.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ],
                configurable: true
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'es'],
                configurable: true
            });
            
            // Remove automation markers
            window.chrome = { runtime: {} };
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Canvas noise
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                const context = originalGetContext.call(this, type, attributes);
                if (type === '2d') {
                    const originalFillText = context.fillText;
                    context.fillText = function(...args) {
                        return originalFillText.apply(this, args);
                    };
                }
                return context;
            };
        """)
        
        if self.config.randomize_user_agent:
            ua = UserAgentPool.get_random()
            await self._context.set_extra_http_headers({"User-Agent": ua})
        
        if self.config.spoof_timezone:
            timezone = TimezoneSpoofer.get_random()
            await self._context.add_init_script(f"""
                Object.defineProperty(Intl.DateTimeFormat, 'resolvedOptions', {{
                    value: () => ({{ timeZone: '{timezone}' }}),
                    configurable: true
                }});
            """)
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> str:
        """Navigate to a URL with stealth."""
        if not self._page:
            raise RuntimeError("Browser not launched. Call launch() first.")
        
        response = await self._page.goto(url, wait_until=wait_until)
        return response.url if response else url
    
    async def click(self, selector: str, delay: int = 0) -> None:
        """Click an element with human-like delay."""
        if delay > 0:
            await asyncio.sleep(delay / 1000)
        await self._page.click(selector)
    
    async def type(self, selector: str, text: str, delay: Tuple[int, int] = (50, 150)) -> None:
        """Type text with human-like delays."""
        await self._page.click(selector)
        for char in text:
            await self._page.type(selector, char, delay=random.uniform(delay[0], delay[1]) / 1000)
    
    async def fill(self, selector: str, text: str) -> None:
        """Fill an input field."""
        await self._page.fill(selector, text)
    
    async def select(self, selector: str, value: str) -> None:
        """Select an option from dropdown."""
        await self._page.select_option(selector, value)
    
    async def hover(self, selector: str) -> None:
        """Hover over an element."""
        await self._page.hover(selector)
    
    async def scroll(self, x: int = 0, y: int = 500) -> None:
        """Scroll the page."""
        await self._page.mouse.wheel(0, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for element to appear."""
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def get_text(self, selector: str) -> str:
        """Get text content."""
        return await self._page.text_content(selector) or ""
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get element attribute."""
        return await self._page.get_attribute(selector, attribute)
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript."""
        return await self._page.evaluate(script)
    
    async def screenshot(self, path: str, full_page: bool = False) -> bytes:
        """Take screenshot."""
        return await self._page.screenshot(path=path, full_page=full_page)
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies."""
        return await self._context.cookies()
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Set cookies."""
        await self._context.add_cookies(cookies)
    
    async def close(self) -> None:
        """Close the browser."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class HumanBehavior:
    """Simulate human-like behavior patterns."""
    
    @staticmethod
    async def human_click(browser: StealthBrowser, selector: str) -> None:
        """Click with human-like movement."""
        box = await browser._page.locator(selector).bounding_box()
        if box:
            x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
            y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
            await browser._page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await browser._page.mouse.click(x, y)
    
    @staticmethod
    async def human_type(browser: StealthBrowser, selector: str, text: str) -> None:
        """Type with human-like delays."""
        await browser._page.click(selector)
        await asyncio.sleep(random.uniform(0.1, 0.2))
        
        for char in text:
            await browser._page.keyboard.type(char, delay=random.uniform(30, 150))
            await asyncio.sleep(random.uniform(0, 50) / 1000)
    
    @staticmethod
    async def human_scroll(browser: StealthBrowser, pages: int = 3) -> None:
        """Scroll down page by page."""
        for _ in range(pages):
            await browser._page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            if random.random() < 0.3:
                await browser._page.evaluate("window.scrollBy(0, -window.innerHeight * 0.3)")
                await asyncio.sleep(random.uniform(0.3, 0.6))
    
    @staticmethod
    async def random_delay(min_ms: int = 100, max_ms: int = 500) -> None:
        """Random delay between actions."""
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)


__all__ = [
    "StealthBrowser",
    "StealthConfig",
    "DetectionLevel",
    "HumanBehavior",
    "UserAgentPool",
    "TimezoneSpoofer",
]
