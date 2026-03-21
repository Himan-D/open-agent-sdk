"""GitHub integration for SmithAI.

Provides:
- Repository management
- Issues and PRs
- Code search
- Actions workflows
- Git operations
"""

from __future__ import annotations

import os
import base64
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class GitHubConfig:
    """GitHub configuration."""
    token: str
    owner: Optional[str] = None
    repo: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "GitHubConfig":
        return cls(
            token=os.environ.get("GITHUB_TOKEN", ""),
            owner=os.environ.get("GITHUB_OWNER"),
            repo=os.environ.get("GITHUB_REPO"),
        )


class GitHubClient:
    """GitHub API client.
    
    Real use cases:
    - Automate issue triage
    - Generate release notes
    - Review code
    - Manage PRs
    - Monitor repos
    - Automate workflows
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig.from_env()
        self._token = self.config.token
        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    
    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self._headers
            )
            return response.json()
    
    async def list_issues(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List issues."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                params=params
            )
            return response.json()
    
    async def create_issue(
        self,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an issue."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an issue."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def close_issue(
        self,
        issue_number: int,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Close an issue."""
        return await self.update_issue(issue_number, state="closed", owner=owner, repo=repo)
    
    async def add_comment(
        self,
        issue_number: int,
        body: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a comment to an issue."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                headers=self._headers,
                json={"body": body}
            )
            return response.json()
    
    async def list_prs(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        state: str = "open",
    ) -> List[Dict[str, Any]]:
        """List pull requests."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=self._headers,
                params={"state": state}
            )
            return response.json()
    
    async def create_pr(
        self,
        title: str,
        head: str,
        base: str,
        body: str = "",
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=self._headers,
                json={
                    "title": title,
                    "head": head,
                    "base": base,
                    "body": body,
                }
            )
            return response.json()
    
    async def get_file(
        self,
        path: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get file contents."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        params = {}
        if ref:
            params["ref"] = ref
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers,
                params=params
            )
            data = response.json()
            
            if "content" in data:
                data["content"] = base64.b64decode(data["content"]).decode()
            
            return data
    
    async def update_file(
        self,
        path: str,
        message: str,
        content: str,
        sha: Optional[str] = None,
        branch: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a file."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        if sha:
            data["sha"] = sha
        if branch:
            data["branch"] = branch
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=self._headers,
                json=data
            )
            return response.json()
    
    async def create_file(
        self,
        path: str,
        message: str,
        content: str,
        branch: Optional[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new file."""
        return await self.update_file(path, message, content, sha=None, branch=branch, owner=owner, repo=repo)
    
    async def search_code(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
    ) -> Dict[str, Any]:
        """Search code."""
        params = {"q": query, "order": order}
        if sort:
            params["sort"] = sort
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/code",
                headers=self._headers,
                params=params
            )
            return response.json()
    
    async def search_issues(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
    ) -> Dict[str, Any]:
        """Search issues and PRs."""
        params = {"q": query, "order": order}
        if sort:
            params["sort"] = sort
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/issues",
                headers=self._headers,
                params=params
            )
            return response.json()
    
    async def get_workflow_runs(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get workflow runs."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        if workflow_id:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/actions/runs"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._headers)
            return response.json()
    
    async def trigger_workflow(
        self,
        workflow_file: str,
        ref: str = "main",
        inputs: Optional[Dict[str, str]] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a workflow."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches",
                headers=self._headers,
                json=data
            )
            return {"status": "triggered" if response.status_code == 204 else "error"}
    
    async def get_commits(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        sha: Optional[str] = None,
        path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get commits."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        
        params = {}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/commits",
                headers=self._headers,
                params=params
            )
            return response.json()


__all__ = ["GitHubClient", "GitHubConfig"]
