"""Jira integration for SmithAI.

Provides:
- Issue management
- Project tracking
- Sprint management
- Workflow operations
"""

from __future__ import annotations

import os
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None


@dataclass
class JiraConfig:
    server: str
    email: str
    api_token: str
    
    @classmethod
    def from_env(cls) -> "JiraConfig":
        return cls(
            server=os.environ.get("JIRA_SERVER", ""),
            email=os.environ.get("JIRA_EMAIL", ""),
            api_token=os.environ.get("JIRA_API_TOKEN", ""),
        )


class JiraClient:
    """Jira API client.
    
    Real use cases:
    - Sprint planning
    - Issue tracking
    - Project management
    - Bug triage
    - Release tracking
    """
    
    def __init__(self, config: Optional[JiraConfig] = None):
        self.config = config or JiraConfig.from_env()
        self._auth = base64.b64encode(
            f"{self.config.email}:{self.config.api_token}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {self._auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search issues using JQL."""
        if not httpx:
            return {}
        
        params = {"jql": jql, "maxResults": max_results}
        if fields:
            params["fields"] = ",".join(fields)
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                "/rest/api/3/search",
                headers=self._headers,
                params=params
            )
            return response.json()
    
    async def get_issue(
        self,
        issue_key: str,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get issue details."""
        if not httpx:
            return {}
        
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                f"/rest/api/3/issue/{issue_key}",
                headers=self._headers,
                params=params
            )
            return response.json()
    
    async def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new issue."""
        if not httpx:
            return {}
        
        data = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue_type},
                "summary": summary,
            }
        }
        
        if description:
            data["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }]
            }
        
        if priority:
            data["fields"]["priority"] = {"name": priority}
        
        if assignee:
            data["fields"]["assignee"] = {"name": assignee}
        
        if labels:
            data["fields"]["labels"] = labels
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.post(
                "/rest/api/3/issue",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def update_issue(
        self,
        issue_key: str,
        fields: Optional[Dict] = None,
        update: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Update an issue."""
        if not httpx:
            return {}
        
        data = {}
        if fields:
            data["fields"] = fields
        if update:
            data["update"] = update
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.put(
                f"/rest/api/3/issue/{issue_key}",
                headers=self._headers,
                json=data
            )
            return response.json() if response.text else {}
    
    async def add_comment(
        self,
        issue_key: str,
        body: str,
    ) -> Dict[str, Any]:
        """Add a comment to an issue."""
        if not httpx:
            return {}
        
        data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}]
                }]
            }
        }
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.post(
                f"/rest/api/3/issue/{issue_key}/comment",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def transition_issue(
        self,
        issue_key: str,
        transition_name: str,
    ) -> Dict[str, Any]:
        """Transition an issue to a new status."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                f"/rest/api/3/issue/{issue_key}/transitions",
                headers=self._headers
            )
            transitions = response.json().get("transitions", [])
        
        transition_id = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break
        
        if not transition_id:
            return {"error": f"Transition '{transition_name}' not found"}
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.post(
                f"/rest/api/3/issue/{issue_key}/transitions",
                headers=self._headers,
                json={"transition": {"id": transition_id}}
            )
            return response.json() if response.text else {"status": "success"}
    
    async def assign_issue(
        self,
        issue_key: str,
        assignee: str,
    ) -> Dict[str, Any]:
        """Assign an issue to a user."""
        if not httpx:
            return {}
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.put(
                f"/rest/api/3/issue/{issue_key}/assignee",
                headers=self._headers,
                json={"name": assignee}
            )
            return response.json() if response.text else {"status": "success"}
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        if not httpx:
            return []
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                "/rest/api/3/project",
                headers=self._headers
            )
            return response.json()
    
    async def get_issue_types(self) -> List[Dict[str, Any]]:
        """Get all issue types."""
        if not httpx:
            return []
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                "/rest/api/3/issuetype",
                headers=self._headers
            )
            return response.json()
    
    async def get_sprints(
        self,
        board_id: str,
        state: str = "active",
    ) -> List[Dict[str, Any]]:
        """Get sprints for a board."""
        if not httpx:
            return []
        
        async with httpx.AsyncClient(base_url=self.config.server) as client:
            response = await client.get(
                f"/rest/agile/1.0/board/{board_id}/sprint",
                headers=self._headers,
                params={"state": state}
            )
            return response.json().get("values", [])


__all__ = ["JiraClient", "JiraConfig"]
