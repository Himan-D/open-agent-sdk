"""Notion integration for OpenAgent.

Real API integration with Notion for databases, pages, and blocks.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class NotionConfig:
    """Notion API configuration."""
    token: str = ""
    database_id: str = ""


class NotionClient:
    """Notion API client."""

    def __init__(self, config: NotionConfig):
        self.config = config
        self.base_url = "https://api.notion.com/v1"
        self._session = None

    async def initialize(self) -> bool:
        """Initialize Notion client."""
        try:
            import httpx
            
            self._session = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.config.token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            logger.info("notion_initialized")
            return True
        except Exception as e:
            logger.error("notion_init_failed", error=str(e))
            return False

    async def close(self):
        """Close the client."""
        if self._session:
            await self._session.aclose()

    async def _post(self, path: str, data: Dict) -> Optional[Dict]:
        """Make POST request."""
        try:
            response = await self._session.post(f"{self.base_url}{path}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("notion_request_failed", path=path, error=str(e))
            return None

    async def _get(self, path: str) -> Optional[Dict]:
        """Make GET request."""
        try:
            response = await self._session.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("notion_get_failed", path=path, error=str(e))
            return None

    async def get_page(self, page_id: str) -> Optional[Dict]:
        """Get a page."""
        return await self._get(f"/pages/{page_id}")

    async def get_database(self, database_id: str) -> Optional[Dict]:
        """Get a database."""
        return await self._get(f"/databases/{database_id}")

    async def query_database(
        self,
        database_id: str,
        filter_props: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100,
    ) -> List[Dict]:
        """Query a database."""
        data = {"page_size": page_size}
        
        if filter_props:
            data["filter"] = filter_props
        if sorts:
            data["sorts"] = sorts

        results = []
        cursor = None

        while True:
            if cursor:
                data["start_cursor"] = cursor

            response = await self._post(f"/databases/{database_id}/query", data)
            if not response:
                break

            results.extend(response.get("results", []))
            
            cursor = response.get("next_cursor")
            if not cursor or not response.get("has_more"):
                break

        return results

    async def create_page(
        self,
        database_id: str,
        properties: Dict,
        children: Optional[List[Dict]] = None,
    ) -> Optional[Dict]:
        """Create a page in a database."""
        data = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        if children:
            data["children"] = children

        return await self._post("/pages", data)

    async def update_page(
        self,
        page_id: str,
        properties: Optional[Dict] = None,
        archived: bool = False,
    ) -> Optional[Dict]:
        """Update a page."""
        data = {"archived": archived}
        if properties:
            data["properties"] = properties

        try:
            response = await self._session.patch(
                f"{self.base_url}/pages/{page_id}",
                json=data,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("notion_update_page_failed", error=str(e))
            return None

    async def append_block_children(
        self,
        block_id: str,
        children: List[Dict],
    ) -> Optional[Dict]:
        """Append blocks to a page."""
        data = {"children": children}
        return await self._post(f"/blocks/{block_id}/children", data)

    async def search(self, query: str, filter_type: str = "page") -> List[Dict]:
        """Search pages and databases."""
        data = {
            "query": query,
            "filter": {"property": "object", "value": filter_type},
        }
        response = await self._post("/search", data)
        return response.get("results", []) if response else []

    def _property_to_text(self, prop: Dict) -> str:
        """Convert Notion property to text."""
        prop_type = prop.get("type", "")
        
        if prop_type == "title":
            return "".join([t.get("plain_text", "") for t in prop.get("title", [])])
        elif prop_type == "rich_text":
            return "".join([t.get("plain_text", "") for t in prop.get("rich_text", [])])
        elif prop_type == "number":
            return str(prop.get("number", ""))
        elif prop_type == "select":
            return prop.get("select", {}).get("name", "")
        elif prop_type == "multi_select":
            return ", ".join([s.get("name", "") for s in prop.get("multi_select", [])])
        elif prop_type == "date":
            return prop.get("date", {}).get("start", "")
        elif prop_type == "checkbox":
            return "Yes" if prop.get("checkbox") else "No"
        elif prop_type == "url":
            return prop.get("url", "")
        elif prop_type == "email":
            return prop.get("email", "")
        elif prop_type == "phone_number":
            return prop.get("phone_number", "")
        
        return ""

    async def get_page_content(self, page_id: str) -> List[Dict]:
        """Get page blocks/content."""
        blocks = []
        cursor = None

        while True:
            path = f"/blocks/{page_id}/children"
            if cursor:
                path += f"?start_cursor={cursor}"

            response = await self._get(path)
            if not response:
                break

            blocks.extend(response.get("results", []))
            
            cursor = response.get("next_cursor")
            if not cursor or not response.get("has_more"):
                break

        return blocks


def create_notion_client(token: str, database_id: str = "") -> NotionClient:
    """Create a Notion client."""
    config = NotionConfig(token=token, database_id=database_id)
    return NotionClient(config)
