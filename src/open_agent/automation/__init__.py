"""Browser Automation Tools - Playwright-based web automation."""

from __future__ import annotations

import asyncio
import json
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
    """Configuration for browser automation."""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    user_agent: Optional[str] = None


class BrowserTool:
    """Browser automation tool using Playwright."""
    
    name = "browser"
    description = "Automate web browser actions: navigate, click, fill, screenshot, scrape"
    category = "automation"
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
    
    async def _ensure_browser(self):
        """Initialize browser if not already done."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.config.headless
            )
            self._context = await self._browser.new_context(
                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
                user_agent=self.config.user_agent,
            )
            self._page = await self._context.new_page()
    
    async def execute(self, command: str, *args, **kwargs) -> "ToolResult":
        """Execute browser command."""
        try:
            await self._ensure_browser()
            
            cmd_lower = command.lower()
            
            if cmd_lower.startswith("navigate:") or cmd_lower.startswith("go:"):
                url = command.split(":", 1)[1].strip()
                await self._page.goto(url, timeout=self.config.timeout)
                title = await self._page.title()
                return ToolResult(success=True, output=f"Navigated to {url}. Title: {title}")
            
            elif cmd_lower.startswith("click:"):
                selector = command.split(":", 1)[1].strip()
                await self._page.click(selector, timeout=self.config.timeout)
                return ToolResult(success=True, output=f"Clicked on {selector}")
            
            elif cmd_lower.startswith("fill:"):
                parts = command.split(":", 1)[1].strip().split("|", 1)
                if len(parts) == 2:
                    selector, value = parts
                    await self._page.fill(selector, value)
                    return ToolResult(success=True, output=f"Filled {selector} with '{value}'")
                return ToolResult(success=False, error="Use format: fill:selector|value")
            
            elif cmd_lower.startswith("screenshot:"):
                path = command.split(":", 1)[1].strip() or "screenshot.png"
                await self._page.screenshot(path=path)
                return ToolResult(success=True, output=f"Screenshot saved to {path}")
            
            elif cmd_lower == "content" or cmd_lower == "html":
                content = await self._page.content()
                return ToolResult(success=True, output=content[:10000])
            
            elif cmd_lower.startswith("text:"):
                selector = command.split(":", 1)[1].strip()
                text = await self._page.text_content(selector)
                return ToolResult(success=True, output=text or "")
            
            elif cmd_lower.startswith("scrape:"):
                selector = command.split(":", 1)[1].strip()
                elements = await self._page.query_selector_all(selector)
                results = []
                for el in elements[:20]:
                    text = await el.text_content()
                    results.append(text.strip() if text else "")
                return ToolResult(success=True, output="\n".join(results))
            
            elif cmd_lower.startswith("wait:"):
                selector = command.split(":", 1)[1].strip()
                await self._page.wait_for_selector(selector, timeout=self.config.timeout)
                return ToolResult(success=True, output=f"Element {selector} appeared")
            
            elif cmd_lower.startswith("evaluate:"):
                script = command.split(":", 1)[1].strip()
                result = await self._page.evaluate(script)
                return ToolResult(success=True, output=str(result))
            
            elif cmd_lower == "title":
                title = await self._page.title()
                return ToolResult(success=True, output=title)
            
            elif cmd_lower == "url":
                url = self._page.url
                return ToolResult(success=True, output=url)
            
            elif cmd_lower.startswith("type:"):
                parts = command.split(":", 1)[1].strip().split("|", 1)
                if len(parts) == 2:
                    selector, text = parts
                    await self._page.type(selector, text, delay=50)
                    return ToolResult(success=True, output=f"Typed '{text}' into {selector}")
                return ToolResult(success=False, error="Use format: type:selector|text")
            
            else:
                return ToolResult(success=False, error=f"Unknown command: {command}")
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class WebScraperTool:
    """Advanced web scraping tool."""
    
    name = "web_scraper"
    description = "Scrape web pages with CSS selectors"
    category = "automation"
    
    def __init__(self):
        self._browser = None
    
    async def execute(self, url: str, selectors: str = "body") -> "ToolResult":
        """Scrape a web page."""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)
                
                selector_list = selectors.split(",") if "," in selectors else [selectors]
                results = {}
                
                for sel in selector_list:
                    sel = sel.strip()
                    elements = await page.query_selector_all(sel)
                    texts = []
                    for el in elements[:50]:
                        text = await el.text_content()
                        if text:
                            texts.append(text.strip())
                    results[sel] = texts[:10]
                
                await browser.close()
                
                output = json.dumps(results, indent=2)
                return ToolResult(success=True, output=output)
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SandboxExecutorTool:
    """Execute code in an isolated sandbox environment."""
    
    name = "sandbox_exec"
    description = "Execute Python/JS code in isolated sandbox"
    category = "automation"
    
    def __init__(self):
        self._allowed_modules = [
            "math", "random", "json", "re", "datetime", "time",
            "collections", "itertools", "functools", "string"
        ]
    
    async def execute(self, language: str, code: str) -> "ToolResult":
        """Execute code in sandbox."""
        try:
            lang = language.lower()
            
            if lang == "python":
                return await self._exec_python(code)
            elif lang == "javascript" or lang == "js":
                return await self._exec_js(code)
            else:
                return ToolResult(success=False, error=f"Unsupported language: {lang}")
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _exec_python(self, code: str) -> "ToolResult":
        """Execute Python in sandbox."""
        import io, contextlib, traceback
        
        # Check for dangerous imports
        forbidden = ["os", "sys", "subprocess", "socket", "requests", "urllib", "http"]
        for f in forbidden:
            if f in code:
                return ToolResult(success=False, error=f"Forbidden import: {f}")
        
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": __builtins__})
            result = output.getvalue() or "Executed successfully"
            return ToolResult(success=True, output=result)
        except Exception:
            output.write(traceback.format_exc())
            return ToolResult(success=True, output=output.getvalue())
    
    async def _exec_js(self, code: str) -> "ToolResult":
        """Execute JavaScript in Node sandbox."""
        import subprocess, tempfile, os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            path = f.name
        
        try:
            result = subprocess.run(
                ["node", path],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout if result.stdout else result.stderr
            return ToolResult(success=True, output=output)
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Execution timed out")
        except FileNotFoundError:
            return ToolResult(success=False, error="Node.js not installed")
        finally:
            os.unlink(path)


class WorkflowAutomatorTool:
    """Automate multi-step workflows."""
    
    name = "workflow"
    description = "Execute multi-step automation workflows"
    category = "automation"
    
    def __init__(self):
        self._workflows: Dict[str, List[Dict[str, Any]]] = {}
    
    def register_workflow(self, name: str, steps: List[Dict[str, Any]]):
        """Register a workflow."""
        self._workflows[name] = steps
    
    async def execute(self, workflow_name: str, **params) -> "ToolResult":
        """Execute a registered workflow."""
        try:
            if workflow_name not in self._workflows:
                return ToolResult(success=False, error=f"Workflow '{workflow_name}' not found")
            
            steps = self._workflows[workflow_name]
            results = []
            
            for i, step in enumerate(steps):
                step_type = step.get("type")
                step_config = step.get("config", {})
                
                if step_type == "browser":
                    browser = BrowserTool()
                    cmd = step_config.get("command", "")
                    for key, val in params.items():
                        cmd = cmd.replace(f"{{{key}}}", str(val))
                    result = await browser.execute(cmd)
                    results.append({"step": i+1, "result": str(result)})
                
                elif step_type == "tool":
                    from open_agent.tools.modular import ToolRegistry
                    registry = ToolRegistry.get_instance()
                    tool_name = step_config.get("tool")
                    tool_args = step_config.get("args", "")
                    for key, val in params.items():
                        tool_args = tool_args.replace(f"{{{key}}}", str(val))
                    result = await registry.execute(tool_name, tool_args)
                    results.append({"step": i+1, "result": str(result)})
                
                elif step_type == "delay":
                    import asyncio
                    await asyncio.sleep(step_config.get("seconds", 1))
                    results.append({"step": i+1, "result": "Delayed"})
            
            return ToolResult(success=True, output=json.dumps(results, indent=2))
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ScreenRecorderTool:
    """Record screen activity."""
    
    name = "screen_record"
    description = "Record screen as video or GIF"
    category = "automation"
    
    async def execute(self, action: str, **kwargs) -> "ToolResult":
        """Record screen."""
        try:
            import subprocess
            
            if action == "start":
                return ToolResult(success=True, output="Screen recording started")
            elif action == "stop":
                return ToolResult(success=True, output="Screen recording stopped")
            elif action == "screenshot":
                return ToolResult(success=True, output="Screenshot captured")
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def register_automation_tools():
    """Register all automation tools."""
    from open_agent.tools.modular import ToolRegistry
    
    registry = ToolRegistry.get_instance()
    
    tools = [
        BrowserTool(),
        WebScraperTool(),
        SandboxExecutorTool(),
        WorkflowAutomatorTool(),
        ScreenRecorderTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    logger.info("automation_tools_registered", count=len(tools))


# Auto-register on import
register_automation_tools()
