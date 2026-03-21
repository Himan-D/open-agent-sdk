"""Notion integration for SmithAI.

Provides:
- Database queries
- Page creation
- Content management
- Block operations
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class NotionConfig:
    api_key: str
    
    @classmethod
    def from_env(cls) -> "NotionConfig":
        return cls(api_key=os.environ.get("NOTION_API_KEY", ""))


class NotionClient:
    """Notion API client.
    
    Real use cases:
    - Task management
    - Knowledge bases
    - Documentation
    - Project tracking
    - Meeting notes
    """
    
    BASE_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"
    
    def __init__(self, config: Optional[NotionConfig] = None):
        self.config = config or NotionConfig.from_env()
        self._headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }
    
    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query a Notion database."""
        if not httpx:
            return []
        
        data = {"page_size": page_size}
        if filter:
            data["filter"] = filter
        if sorts:
            data["sorts"] = sorts
        
        results = []
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/databases/{database_id}/query",
                headers=self._headers,
                json=data
            )
            page = response.json()
            results.extend(page.get("results", []))
            
            while page.get("has_more"):
                data["start_cursor"] = page.get("next_cursor")
                response = await client.post(
                    f"{self.BASE_URL}/databases/{database_id}/query",
                    headers=self._headers,
                    json=data
                )
                page = response.json()
                results.extend(page.get("results", []))
        
        return results
    
    async def create_page(
        self,
        parent_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None,
        is_database_page: bool = False,
    ) -> Dict[str, Any]:
        """Create a new page."""
        if not httpx:
            return {}
        
        if is_database_page:
            data = {
                "parent": {"database_id": parent_id},
                "properties": properties,
            }
        else:
            data = {
                "parent": {"page_id": parent_id},
                "properties": properties,
            }
        
        if children:
            data["children"] = children
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/pages",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def update_page(
        self,
        page_id: str,
        properties: Optional[Dict] = None,
        archived: bool = False,
    ) -> Dict[str, Any]:
        """Update a page."""
        if not httpx:
            return {}
        
        data = {"archived": archived}
        if properties:
            data["properties"] = properties
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.BASE_URL}/pages/{page_id}",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a page."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/pages/{page_id}",
                headers=self._headers
            )
            return response.json()
    
    async def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """Get children of a block."""
        if not httpx:
            return []
        
        results = []
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/blocks/{block_id}/children",
                headers=self._headers
            )
            page = response.json()
            results.extend(page.get("results", []))
            
            while page.get("has_more"):
                response = await client.get(
                    f"{self.BASE_URL}/blocks/{block_id}/children",
                    headers=self._headers,
                    params={"start_cursor": page.get("next_cursor")}
                )
                page = response.json()
                results.extend(page.get("results", []))
        
        return results
    
    async def append_block_children(
        self,
        block_id: str,
        children: List[Dict],
    ) -> Dict[str, Any]:
        """Append children to a block."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.BASE_URL}/blocks/{block_id}/children",
                headers=self._headers,
                json={"children": children}
            )
            return response.json()
    
    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new database."""
        if not httpx:
            return {}
        
        data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/databases",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def search(self, query: str, filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search pages and databases."""
        if not httpx:
            return []
        
        data = {"query": query}
        if filter:
            data["filter"] = filter
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/search",
                headers=self._headers,
                json=data
            )
            return response.json().get("results", [])


class NotionBlockBuilder:
    """Helper to build Notion blocks."""
    
    @staticmethod
    def heading(text: str, level: int = 1) -> Dict:
        return {
            "type": f"heading_{level}",
            f"heading_{level}": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def paragraph(text: str) -> Dict:
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def bulleted_list_item(text: str) -> Dict:
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def numbered_list_item(text: str) -> Dict:
        return {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def code_block(code: str, language: str = "python") -> Dict:
        return {
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language
            }
        }
    
    @staticmethod
    def quote(text: str) -> Dict:
        return {
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    @staticmethod
    def divider() -> Dict:
        return {"type": "divider", "divider": {}}
    
    @staticmethod
    def todo(text: str, checked: bool = False) -> Dict:
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked
            }
        }


__all__ = ["NotionClient", "NotionConfig", "NotionBlockBuilder"]
