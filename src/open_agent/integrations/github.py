"""GitHub integration for OpenAgent.

Real API integration with GitHub for issues, PRs, repos, and more.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class GitHubConfig:
    """GitHub API configuration."""
    token: str = ""
    username: str = ""
    owner: str = ""


class GitHubClient:
    """GitHub API client."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self.base_url = "https://api.github.com"
        self._session = None

    async def initialize(self) -> bool:
        """Initialize GitHub client."""
        try:
            import httpx
            
            self._session = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.config.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
            logger.info("github_initialized")
            return True
        except Exception as e:
            logger.error("github_init_failed", error=str(e))
            return False

    async def close(self):
        """Close the client."""
        if self._session:
            await self._session.aclose()

    async def _get(self, path: str) -> Optional[Dict]:
        """Make GET request."""
        try:
            response = await self._session.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_request_failed", path=path, error=str(e))
            return None

    async def _post(self, path: str, data: Dict) -> Optional[Dict]:
        """Make POST request."""
        try:
            response = await self._session.post(f"{self.base_url}{path}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_post_failed", path=path, error=str(e))
            return None

    async def get_user(self) -> Optional[Dict]:
        """Get current user info."""
        return await self._get("/user")

    async def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository info."""
        return await self._get(f"/repos/{owner}/{repo}")

    async def list_repos(self, per_page: int = 30) -> List[Dict]:
        """List user repositories."""
        data = await self._get(f"/user/repos?per_page={per_page}")
        return data if isinstance(data, list) else []

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> List[Dict]:
        """List issues in a repository."""
        data = await self._get(f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}")
        return [i for i in (data or []) if "pull_request" not in i]  # Filter out PRs

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Create an issue."""
        data = {
            "title": title,
            "body": body,
        }
        if labels:
            data["labels"] = labels
        return await self._post(f"/repos/{owner}/{repo}/issues", data)

    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict]:
        """Get issue details."""
        return await self._get(f"/repos/{owner}/{repo}/issues/{issue_number}")

    async def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Update an issue."""
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels

        try:
            response = await self._session.patch(
                f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}",
                json=data,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_update_issue_failed", error=str(e))
            return None

    async def add_issue_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> Optional[Dict]:
        """Add a comment to an issue."""
        return await self._post(
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            {"body": body},
        )

    async def list_pulls(
        self,
        owner: str,
        repo: str,
        state: str = "open",
    ) -> List[Dict]:
        """List pull requests."""
        return await self._get(f"/repos/{owner}/{repo}/pulls?state={state}") or []

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
    ) -> Optional[Dict]:
        """Create a pull request."""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        return await self._post(f"/repos/{owner}/{repo}/pulls", data)

    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict]:
        """Get PR details."""
        return await self._get(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    async def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> Optional[Dict]:
        """Merge a pull request."""
        data = {}
        if commit_title:
            data["commit_title"] = commit_title
        if commit_message:
            data["commit_message"] = commit_message

        try:
            response = await self._session.put(
                f"{self.base_url}/repos/{owner}/{repo}/merges",
                json=data,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_merge_failed", error=str(e))
            return None

    async def list_commits(
        self,
        owner: str,
        repo: str,
        per_page: int = 30,
    ) -> List[Dict]:
        """List commits in a repository."""
        data = await self._get(f"/repos/{owner}/{repo}/commits?per_page={per_page}")
        return data if isinstance(data, list) else []

    async def get_commit(self, owner: str, repo: str, sha: str) -> Optional[Dict]:
        """Get commit details."""
        return await self._get(f"/repos/{owner}/{repo}/commits/{sha}")

    async def list_branches(self, owner: str, repo: str) -> List[Dict]:
        """List branches in a repository."""
        data = await self._get(f"/repos/{owner}/{repo}/branches")
        return data if isinstance(data, list) else []

    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        from_branch: str = "main",
    ) -> Optional[Dict]:
        """Create a new branch."""
        try:
            # Get the SHA of the source branch
            ref_data = await self._get(f"/repos/{owner}/{repo}/git/ref/heads/{from_branch}")
            if not ref_data:
                return None

            sha = ref_data.get("object", {}).get("sha")
            if not sha:
                return None

            # Create the new branch
            response = await self._session.post(
                f"{self.base_url}/repos/{owner}/{repo}/git/refs",
                json={
                    "ref": f"refs/heads/{branch}",
                    "sha": sha,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_create_branch_failed", error=str(e))
            return None

    async def create_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Optional[Dict]:
        """Create or update a file."""
        import base64

        try:
            data = {
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch,
            }
            return await self._put(f"/repos/{owner}/{repo}/contents/{path}", data)
        except Exception as e:
            logger.error("github_create_file_failed", error=str(e))
            return None

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[str]:
        """Get file content."""
        import base64

        try:
            path_param = f"/repos/{owner}/{repo}/contents/{path}"
            if ref:
                path_param += f"?ref={ref}"

            data = await self._get(path_param)
            if data and "content" in data:
                content = data["content"].replace("\n", "")
                return base64.b64decode(content).decode()
        except Exception as e:
            logger.error("github_get_file_failed", error=str(e))
        return None

    async def _put(self, path: str, data: Dict) -> Optional[Dict]:
        """Make PUT request."""
        try:
            response = await self._session.put(f"{self.base_url}{path}", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("github_put_failed", path=path, error=str(e))
            return None

    async def search_repos(self, query: str, per_page: int = 30) -> List[Dict]:
        """Search repositories."""
        import httpx
        encoded_query = httpx.QueryParams({"q": query, "per_page": str(per_page)})
        
        try:
            response = await self._session.get(
                f"{self.base_url}/search/repositories",
                params=encoded_query,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error("github_search_failed", error=str(e))
            return []

    async def search_issues(self, query: str, per_page: int = 30) -> List[Dict]:
        """Search issues and PRs."""
        import httpx
        encoded_query = httpx.QueryParams({"q": query, "per_page": str(per_page)})
        
        try:
            response = await self._session.get(
                f"{self.base_url}/search/issues",
                params=encoded_query,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except Exception as e:
            logger.error("github_search_issues_failed", error=str(e))
            return []


def create_github_client(token: str, username: str = "") -> GitHubClient:
    """Create a GitHub client."""
    config = GitHubConfig(token=token, username=username)
    return GitHubClient(config)
