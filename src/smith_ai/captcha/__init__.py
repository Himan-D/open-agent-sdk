"""Captcha Bypass - Handle reCAPTCHA, hCaptcha, Cloudflare challenges.

This module provides captcha solving capabilities:
- reCAPTCHA v2/v3
- hCaptcha
- Cloudflare Turnstile
- Image captchas via 2Captcha/Anti-Captcha
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class CaptchaType(Enum):
    RECAPTCHA_V2 = "recaptcha-v2"
    RECAPTCHA_V3 = "recaptcha-v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE = "image"
    TEXT = "text"


@dataclass
class CaptchaConfig:
    """Configuration for captcha solving."""
    api_key: Optional[str] = None
    provider: str = "2captcha"
    timeout: int = 120
    max_retries: int = 3
    

class CaptchaSolver:
    """Solve captchas using external APIs.
    
    Supported providers:
    - 2Captcha (https://2captcha.com)
    - Anti-Captcha (https://anti-captcha.com)
    - CapMonster (https://capmonster.cloud)
    
    Real use cases:
    - Automate account registration
    - Bypass login forms
    - Access restricted content
    - Price aggregation
    - Lead generation
    """
    
    PROVIDER_URLS = {
        "2captcha": "https://2captcha.com",
        "anticaptcha": "https://anti-captcha.com",
        "capmonster": "https://capmonster.cloud",
    }
    
    def __init__(self, config: Optional[CaptchaConfig] = None):
        self.config = config or CaptchaConfig()
        self._api_key = self.config.api_key or os.getenv("CAPTCHA_API_KEY")
    
    async def solve_recaptcha(
        self,
        site_key: str,
        url: str,
        version: str = "v2"
    ) -> Optional[str]:
        """Solve reCAPTCHA (v2 or v3).
        
        Args:
            site_key: The site key from the website
            url: The URL where captcha appears
            version: 'v2' or 'v3'
        """
        if not self._api_key:
            return await self._solve_manually(site_key, url, CaptchaType.RECAPTCHA_V2)
        
        captcha_type = "4" if version == "v3" else "1"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                submit_url = f"{self.PROVIDER_URLS.get(self.config.provider)}/in.php"
                data = {
                    "key": self._api_key,
                    "method": "userrecaptcha",
                    "googlekey": site_key,
                    "pageurl": url,
                    "version": version,
                }
                
                response = await client.post(submit_url, data=data)
                result = response.text
                
                if "OK|" not in result:
                    return None
                
                captcha_id = result.split("|")[1]
                return await self._wait_for_result(captcha_id)
        
        except Exception:
            return None
    
    async def solve_hcaptcha(
        self,
        site_key: str,
        url: str
    ) -> Optional[str]:
        """Solve hCaptcha."""
        if not self._api_key:
            return await self._solve_manually(site_key, url, CaptchaType.HCAPTCHA)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                submit_url = f"{self.PROVIDER_URLS.get(self.config.provider)}/in.php"
                data = {
                    "key": self._api_key,
                    "method": "hcaptcha",
                    "sitekey": site_key,
                    "pageurl": url,
                }
                
                response = await client.post(submit_url, data=data)
                result = response.text
                
                if "OK|" not in result:
                    return None
                
                captcha_id = result.split("|")[1]
                return await self._wait_for_result(captcha_id)
        
        except Exception:
            return None
    
    async def solve_turnstile(
        self,
        site_key: str,
        url: str
    ) -> Optional[str]:
        """Solve Cloudflare Turnstile."""
        if not self._api_key:
            return await self._solve_manually(site_key, url, CaptchaType.TURNSTILE)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                submit_url = f"{self.PROVIDER_URLS.get(self.config.provider)}/in.php"
                data = {
                    "key": self._api_key,
                    "method": "turnstile",
                    "sitekey": site_key,
                    "pageurl": url,
                }
                
                response = await client.post(submit_url, data=data)
                result = response.text
                
                if "OK|" not in result:
                    return None
                
                captcha_id = result.split("|")[1]
                return await self._wait_for_result(captcha_id)
        
        except Exception:
            return None
    
    async def solve_image(
        self,
        image_base64: str
    ) -> Optional[str]:
        """Solve image captcha from base64 image."""
        if not self._api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                submit_url = f"{self.PROVIDER_URLS.get(self.config.provider)}/in.php"
                data = {
                    "key": self._api_key,
                    "method": "base64",
                    "body": image_base64,
                }
                
                response = await client.post(submit_url, data=data)
                result = response.text
                
                if "OK|" not in result:
                    return None
                
                captcha_id = result.split("|")[1]
                return await self._wait_for_result(captcha_id)
        
        except Exception:
            return None
    
    async def _wait_for_result(self, captcha_id: str) -> Optional[str]:
        """Poll for captcha result."""
        result_url = f"{self.PROVIDER_URLS.get(self.config.provider)}/res.php"
        
        for _ in range(self.config.timeout // 5):
            await asyncio.sleep(5)
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(result_url, params={
                        "key": self._api_key,
                        "action": "get",
                        "id": captcha_id,
                    })
                    
                    result = response.text
                    
                    if result == "CAPCHA_NOT_READY":
                        continue
                    
                    if "OK|" in result:
                        return result.split("|")[1]
                    
                    return None
            
            except Exception:
                continue
        
        return None
    
    async def _solve_manually(
        self,
        site_key: str,
        url: str,
        captcha_type: CaptchaType
    ) -> Optional[str]:
        """Manual solving fallback (for testing)."""
        return None


class CaptchaDetector:
    """Detect captcha challenges on web pages."""
    
    RECAPTCHA_SELECTORS = [
        ".g-recaptcha",
        "[data-sitekey]",
        "#recaptcha",
        ".rc-anchor",
    ]
    
    HCAPTCHA_SELECTORS = [
        ".h-captcha",
        "[data-hcaptcha-sitekey]",
        "#hcaptcha",
    ]
    
    TURNSTILE_SELECTORS = [
        ".cf-turnstile",
        "[data-sitekey]",
        "#turnstile",
    ]
    
    CLOUDFLARE_SELECTORS = [
        "#challenge-running",
        ".challenge-running",
        "#cf-challenge-running",
        "[data-ray]",
    ]
    
    @staticmethod
    async def detect(page) -> Optional[CaptchaType]:
        """Detect if page has a captcha challenge."""
        content = await page.content()
        
        for selector in CaptchaDetector.RECAPTCHA_SELECTORS:
            if await page.query_selector(selector):
                return CaptchaType.RECAPTCHA_V2
        
        for selector in CaptchaDetector.HCAPTCHA_SELECTORS:
            if await page.query_selector(selector):
                return CaptchaType.HCAPTCHA
        
        for selector in CaptchaDetector.TURNSTILE_SELECTORS:
            if await page.query_selector(selector):
                return CaptchaType.TURNSTILE
        
        for selector in CaptchaDetector.CLOUDFLARE_SELECTORS:
            if await page.query_selector(selector):
                return CaptchaType.TURNSTILE
        
        if "recaptcha" in content.lower():
            return CaptchaType.RECAPTCHA_V2
        if "hcaptcha" in content.lower():
            return CaptchaType.HCAPTCHA
        
        return None
    
    @staticmethod
    async def get_site_key(page, captcha_type: CaptchaType) -> Optional[str]:
        """Extract site key from page."""
        selectors = {
            CaptchaType.RECAPTCHA_V2: "[data-sitekey]",
            CaptchaType.HCAPTCHA: "[data-hcaptcha-sitekey]",
            CaptchaType.TURNSTILE: "[data-sitekey]",
        }
        
        selector = selectors.get(captcha_type)
        if not selector:
            return None
        
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.get_attribute("data-sitekey")
        except:
            pass
        
        return None


class CaptchaAutomation:
    """High-level captcha automation with browser."""
    
    def __init__(
        self,
        browser=None,
        solver: Optional[CaptchaSolver] = None
    ):
        self.browser = browser
        self.solver = solver or CaptchaSolver()
    
    async def handle_captcha(self, page) -> bool:
        """Automatically detect and solve captcha on page."""
        captcha_type = await CaptchaDetector.detect(page)
        
        if not captcha_type:
            return True
        
        url = page.url
        site_key = await CaptchaDetector.get_site_key(page, captcha_type)
        
        if not site_key:
            return False
        
        if captcha_type == CaptchaType.RECAPTCHA_V2:
            token = await self.solver.solve_recaptcha(site_key, url, "v2")
        elif captcha_type == CaptchaType.HCAPTCHA:
            token = await self.solver.solve_hcaptcha(site_key, url)
        elif captcha_type == CaptchaType.TURNSTILE:
            token = await self.solver.solve_turnstile(site_key, url)
        else:
            return False
        
        if token:
            await self._submit_token(page, captcha_type, token)
            return True
        
        return False
    
    async def _submit_token(
        self,
        page,
        captcha_type: CaptchaType,
        token: str
    ) -> None:
        """Submit solved captcha token."""
        if captcha_type == CaptchaType.RECAPTCHA_V2:
            await page.evaluate(f"""
                document.querySelector('[name="g-recaptcha-response"]').innerHTML = '{token}';
                if (typeof ___grecaptcha_cfg !== 'undefined') {{
                    ___grecaptcha_cfg.clients['0']['0']['0'].r = '{{e: null, r: {{}}}}';
                }}
            """)
            
            try:
                callback = await page.query_selector("[data-callback]")
                if callback:
                    await callback.evaluate(f"el => el.click()")
            except:
                pass
        
        elif captcha_type == CaptchaType.HCAPTCHA:
            await page.evaluate(f"""
                document.querySelector('[name="h-captcha-response"]').innerHTML = '{token}';
            """)
        
        elif captcha_type == CaptchaType.TURNSTILE:
            await page.evaluate(f"""
                document.querySelector('[name="cf-turnstile-response"]').innerHTML = '{token}';
                if (typeof turnstile !== 'undefined') {{
                    turnstile.reset();
                }}
            """)


__all__ = [
    "CaptchaSolver",
    "CaptchaDetector",
    "CaptchaAutomation",
    "CaptchaType",
    "CaptchaConfig",
]
