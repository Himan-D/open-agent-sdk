"""Integration modules for SmithAI.

Provides integrations with:
- GitHub: Issues, PRs, repos, actions
- Slack: Messaging, channels, webhooks
- Discord: Webhooks, bots
- Notion: Databases, pages
- Jira: Issues, projects
- Google: Calendar, Drive, Gmail
- Twitter/X: Posting, timeline
- LinkedIn: Messaging, profile
"""

from smith_ai.integrations.github import GitHubClient, GitHubConfig
from smith_ai.integrations.slack import SlackClient, SlackWebhook
from smith_ai.integrations.discord import DiscordWebhook, DiscordBot
from smith_ai.integrations.notion import NotionClient, NotionConfig
from smith_ai.integrations.jira import JiraClient, JiraConfig
from smith_ai.integrations.google import GoogleWorkspace, GoogleConfig

__all__ = [
    "GitHubClient",
    "GitHubConfig",
    "SlackClient",
    "SlackWebhook",
    "DiscordWebhook",
    "DiscordBot",
    "NotionClient",
    "NotionConfig",
    "JiraClient",
    "JiraConfig",
    "GoogleWorkspace",
    "GoogleConfig",
]
