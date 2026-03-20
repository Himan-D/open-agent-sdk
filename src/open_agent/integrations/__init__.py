"""Integrations module for OpenAgent."""

from open_agent.integrations.google import (
    GoogleWorkspace,
    GoogleOAuthFlow,
    GoogleOAuthConfig,
    GoogleTokens,
    GoogleServices,
    GmailTool,
    CalendarTool,
    DriveTool,
    create_google_workspace,
)

from open_agent.integrations.github import (
    GitHubClient,
    GitHubConfig,
    create_github_client,
)

from open_agent.integrations.notion import (
    NotionClient,
    NotionConfig,
    create_notion_client,
)

__all__ = [
    # Google
    "GoogleWorkspace",
    "GoogleOAuthFlow",
    "GoogleOAuthConfig",
    "GoogleTokens",
    "GoogleServices",
    "GmailTool",
    "CalendarTool",
    "DriveTool",
    "create_google_workspace",
    # GitHub
    "GitHubClient",
    "GitHubConfig",
    "create_github_client",
    # Notion
    "NotionClient",
    "NotionConfig",
    "create_notion_client",
]
