"""Full Browser Automation - Complete Browserbase-like functionality."""

from __future__ import annotations

import asyncio
import json
import base64
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.success:
            return self.output
        return f"Error: {self.error}"


@dataclass
class BrowserConfig:
    """Browser configuration."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    user_agent: Optional[str] = None


class BrowserTool:
    """Complete browser automation tool - full Browserbase functionality.
    
    Commands:
        navigate:<url>       - Navigate to URL
        click:<selector>     - Click element
        dblclick:<selector>  - Double click element
        rightclick:<selector> - Right click element
        fill:<selector>|<text> - Fill input field
        type:<selector>|<text> - Type text with delay
        select:<selector>|<value> - Select dropdown option
        check:<selector>      - Check checkbox
        uncheck:<selector>   - Uncheck checkbox
        hover:<selector>      - Hover over element
        screenshot           - Take screenshot
        screenshot:path       - Save screenshot to path
        content              - Get page HTML
        text:<selector>      - Get element text
        html:<selector>      - Get element HTML
        attribute:<selector>|<attr> - Get element attribute
        exists:<selector>    - Check if element exists
        visible:<selector>   - Check if element is visible
        enabled:<selector>   - Check if element is enabled
        count:<selector>     - Count matching elements
        wait:<selector>     - Wait for element
        wait:<seconds>      - Wait for seconds
        wait_for_navigation - Wait for page navigation
        evaluate:<js>        - Execute JavaScript
        press:<key>          - Press keyboard key
        press:<selector>|<key> - Focus and press key
        upload:<selector>|<file> - Upload file
        go_back             - Go back in history
        go_forward          - Go forward in history
        reload              - Reload page
        pdf                 - Generate PDF
        cookies             - Get cookies
        set_cookie:<name>|<value>|<domain> - Set cookie
        delete_cookies      - Delete all cookies
        clear               - Clear input
        submit:<selector>   - Submit form
        inner_text:<selector> - Get inner text
        scroll:<selector>   - Scroll to element
        scroll:0|<y>        - Scroll to position
        select_all:<selector> - Select all text
        copy                 - Copy to clipboard
        paste                - Paste from clipboard
    """
    
    name = "browser"
    description = "Complete browser automation - DOM, forms, clicks, scraping"
    category = "automation"
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
        self._responses = []
    
    async def _ensure_browser(self):
        """Initialize browser."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.config.headless)
            self._context = await self._browser.new_context(
                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
                user_agent=self.config.user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            self._page = await self._context.new_page()
            self._page.on("response", lambda r: self._responses.append(r.url))
    
    async def execute(self, command: str) -> ToolResult:
        """Execute browser command."""
        try:
            await self._ensure_browser()
            
            parts = command.split(":", 1)
            if len(parts) < 2:
                cmd, arg = parts[0] if parts else "", ""
            else:
                cmd, arg = parts[0].lower(), parts[1]
            
            # Navigation
            if cmd in ("navigate", "goto", "go", "load"):
                return await self._navigate(arg)
            
            # Clicks
            elif cmd == "click":
                await self._page.click(arg, timeout=self.config.timeout)
                return ToolResult(success=True, output=f"Clicked {arg}")
            
            elif cmd == "dblclick":
                await self._page.dblclick(arg, timeout=self.config.timeout)
                return ToolResult(success=True, output=f"Double-clicked {arg}")
            
            elif cmd == "rightclick":
                await self._page.click(arg, button="right", timeout=self.config.timeout)
                return ToolResult(success=True, output=f"Right-clicked {arg}")
            
            # Fill & Type
            elif cmd == "fill":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    await self._page.fill(parts[0], parts[1])
                    return ToolResult(success=True, output=f"Filled {parts[0]}")
                return ToolResult(success=False, error="Use: fill:selector|text")
            
            elif cmd == "type":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    await self._page.type(parts[0], parts[1], delay=50)
                    return ToolResult(success=True, output=f"Typed into {parts[0]}")
                return ToolResult(success=False, error="Use: type:selector|text")
            
            elif cmd == "press":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    await self._page.click(parts[0])
                    await self._page.keyboard.press(parts[1])
                else:
                    await self._page.keyboard.press(arg)
                return ToolResult(success=True, output=f"Pressed {arg}")
            
            # Select
            elif cmd == "select":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    await self._page.select_option(parts[0], parts[1])
                    return ToolResult(success=True, output=f"Selected {parts[1]} in {parts[0]}")
                return ToolResult(success=False, error="Use: select:selector|value")
            
            # Checkbox
            elif cmd == "check":
                await self._page.check(arg)
                return ToolResult(success=True, output=f"Checked {arg}")
            
            elif cmd == "uncheck":
                await self._page.uncheck(arg)
                return ToolResult(success=True, output=f"Unchecked {arg}")
            
            # Hover & Scroll
            elif cmd == "hover":
                await self._page.hover(arg)
                return ToolResult(success=True, output=f"Hovered {arg}")
            
            elif cmd == "scroll":
                if "|" in arg:
                    _, y = arg.split("|", 1)
                    await self._page.evaluate(f"window.scrollTo(0, {y})")
                else:
                    await self._page.evaluate(f"document.querySelector('{arg}').scrollIntoView()")
                return ToolResult(success=True, output=f"Scrolled to {arg}")
            
            # Screenshot
            elif cmd == "screenshot":
                path = arg if arg else "screenshot.png"
                await self._page.screenshot(path=path, full_page=True)
                return ToolResult(success=True, output=f"Screenshot saved to {path}")
            
            # Content
            elif cmd in ("content", "html"):
                content = await self._page.content()
                return ToolResult(success=True, output=content[:50000])
            
            elif cmd == "text":
                text = await self._page.text_content(arg)
                return ToolResult(success=True, output=text or "")
            
            elif cmd == "inner_text":
                text = await self._page.inner_text(arg)
                return ToolResult(success=True, output=text or "")
            
            elif cmd == "attribute":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    attr = await self._page.get_attribute(parts[0], parts[1])
                    return ToolResult(success=True, output=attr or "")
                return ToolResult(success=False, error="Use: attribute:selector|attr")
            
            # Element state
            elif cmd == "exists":
                el = await self._page.query_selector(arg)
                return ToolResult(success=True, output=str(el is not None))
            
            elif cmd == "visible":
                el = await self._page.query_selector(arg)
                if el:
                    visible = await el.is_visible()
                    return ToolResult(success=True, output=str(visible))
                return ToolResult(success=True, output="false")
            
            elif cmd == "enabled":
                el = await self._page.query_selector(arg)
                if el:
                    enabled = await el.is_enabled()
                    return ToolResult(success=True, output=str(enabled))
                return ToolResult(success=True, output="false")
            
            elif cmd == "count":
                els = await self._page.query_selector_all(arg)
                return ToolResult(success=True, output=str(len(els)))
            
            # Wait
            elif cmd == "wait":
                try:
                    seconds = int(arg)
                    await asyncio.sleep(seconds)
                    return ToolResult(success=True, output=f"Waited {seconds}s")
                except ValueError:
                    await self._page.wait_for_selector(arg, timeout=self.config.timeout)
                    return ToolResult(success=True, output=f"Element {arg} appeared")
            
            elif cmd == "wait_for_navigation":
                await self._page.wait_for_load_state("networkidle")
                return ToolResult(success=True, output="Navigation complete")
            
            # JavaScript
            elif cmd == "evaluate":
                result = await self._page.evaluate(arg)
                return ToolResult(success=True, output=str(result))
            
            # Navigation
            elif cmd == "go_back":
                await self._page.go_back()
                return ToolResult(success=True, output="Went back")
            
            elif cmd == "go_forward":
                await self._page.go_forward()
                return ToolResult(success=True, output="Went forward")
            
            elif cmd == "reload":
                await self._page.reload()
                return ToolResult(success=True, output="Reloaded")
            
            # Form
            elif cmd == "clear":
                await self._page.fill(arg, "")
                return ToolResult(success=True, output=f"Cleared {arg}")
            
            elif cmd == "submit":
                await self._page.click(f"{arg} button[type='submit']")
                return ToolResult(success=True, output=f"Submitted form {arg}")
            
            elif cmd == "select_all":
                await self._page.keyboard.press("Control+a") if "win" not in self.config.user_agent else await self._page.keyboard.press("Meta+a")
                return ToolResult(success=True, output="Selected all")
            
            # Cookies
            elif cmd == "cookies":
                cookies = await self._context.cookies()
                return ToolResult(success=True, output=json.dumps(cookies, indent=2))
            
            elif cmd == "delete_cookies":
                await self._context.clear_cookies()
                return ToolResult(success=True, output="Cookies deleted")
            
            elif cmd == "set_cookie":
                parts = arg.split("|")
                if len(parts) >= 3:
                    await self._context.add_cookies([{
                        "name": parts[0],
                        "value": parts[1],
                        "domain": parts[2]
                    }])
                    return ToolResult(success=True, output=f"Cookie set: {parts[0]}")
                return ToolResult(success=False, error="Use: set_cookie:name|value|domain")
            
            # PDF
            elif cmd == "pdf":
                path = arg if arg else "page.pdf"
                await self._page.pdf(path=path)
                return ToolResult(success=True, output=f"PDF saved to {path}")
            
            # Info
            elif cmd == "title":
                return ToolResult(success=True, output=await self._page.title())
            
            elif cmd == "url":
                return ToolResult(success=True, output=self._page.url)
            
            elif cmd == "requests":
                return ToolResult(success=True, output=json.dumps(self._responses[-20:]))
            
            # Scrape multiple
            elif cmd == "scrape":
                els = await self._page.query_selector_all(arg)
                results = []
                for el in els[:50]:
                    text = await el.text_content()
                    if text:
                        results.append(text.strip())
                return ToolResult(success=True, output="\n".join(results))
            
            # Upload
            elif cmd == "upload":
                parts = arg.split("|", 1)
                if len(parts) == 2:
                    file_input = await self._page.query_selector(parts[0])
                    await file_input.set_input_files(parts[1])
                    return ToolResult(success=True, output=f"Uploaded {parts[1]} to {parts[0]}")
                return ToolResult(success=False, error="Use: upload:selector|file")
            
            else:
                return ToolResult(success=False, error=f"Unknown command: {cmd}")
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _navigate(self, url: str) -> ToolResult:
        """Navigate to URL."""
        response = await self._page.goto(url, timeout=self.config.timeout)
        status = response.status if response else "N/A"
        title = await self._page.title()
        return ToolResult(
            success=True, 
            output=f"Loaded {url} (Status: {status}, Title: {title})",
            metadata={"url": url, "status": status, "title": title}
        )
    
    async def close(self):
        """Close browser."""
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class WebScraperTool:
    """Advanced web scraper with selectors."""
    
    name = "scrape"
    description = "Scrape web pages - scrape:url|selector1,selector2"
    category = "automation"
    
    async def execute(self, input_str: str) -> ToolResult:
        """Scrape web page."""
        try:
            parts = input_str.split("|")
            url = parts[0].strip()
            selectors = parts[1].split(",") if len(parts) > 1 else ["body"]
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                
                results = {}
                for sel in selectors:
                    sel = sel.strip()
                    elements = await page.query_selector_all(sel)
                    texts = []
                    for el in elements[:100]:
                        text = await el.text_content()
                        if text:
                            texts.append(text.strip())
                    results[sel] = texts[:20]
                
                await browser.close()
                return ToolResult(success=True, output=json.dumps(results, indent=2))
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FormFillerTool:
    """Auto-fill forms with data."""
    
    name = "fill_form"
    description = "Fill form fields - fill_form:url|field1:value1,field2:value2"
    category = "automation"
    
    async def execute(self, input_str: str) -> ToolResult:
        """Fill form."""
        try:
            parts = input_str.split("|")
            url = parts[0].strip()
            fields = {}
            if len(parts) > 1:
                for pair in parts[1].split(","):
                    kv = pair.split(":", 1)
                    if len(kv) == 2:
                        fields[kv[0].strip()] = kv[1].strip()
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                
                for selector, value in fields.items():
                    try:
                        await page.fill(selector, value)
                    except Exception:
                        try:
                            await page.select_option(selector, value)
                        except Exception:
                            pass
                
                content = await page.content()
                await browser.close()
                
                return ToolResult(
                    success=True, 
                    output=f"Filled {len(fields)} fields on {url}",
                    metadata={"fields": fields}
                )
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register():
    """Register all browser tools."""
    from open_agent.tools.modular import ToolRegistry
    
    registry = ToolRegistry.get_instance()
    registry.register(BrowserTool())
    registry.register(WebScraperTool())
    registry.register(FormFillerTool())
    
    logger.info("browser_tools_registered")


register()
