"""Browser sandbox module - Browser automation for agents.

This module provides browser sandbox functionality similar to OpenClaw:
- Playwright-based browser automation
- Screenshot capture
- Web scraping
- Form filling
"""

from open_agent.sandbox.browser import (
    BrowserSandbox, BrowserConfig, BrowserType, BrowserAction,
    BrowserResult, create_browser_sandbox
)

__all__ = [
    "BrowserSandbox",
    "BrowserConfig",
    "BrowserType",
    "BrowserAction",
    "BrowserResult",
    "create_browser_sandbox",
]
