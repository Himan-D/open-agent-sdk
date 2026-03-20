"""Built-in tools for agents."""

from typing import Optional, List, Dict, Any, Type
from dataclasses import dataclass
import json
import structlog

from open_agent.agents.tools.base import BaseTool

logger = structlog.get_logger(__name__)


@dataclass
class CalculatorTool(BaseTool):
    """Calculator tool for mathematical operations."""
    
    name: str = "calculator"
    description: str = "Performs mathematical calculations. Input should be a mathematical expression."
    
    def execute(self, expression: str) -> str:
        """Execute a mathematical expression."""
        try:
            import re
            safe_dict = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": __import__("math").sqrt,
                "sin": __import__("math").sin, "cos": __import__("math").cos,
                "tan": __import__("math").tan, "log": __import__("math").log,
                "pi": __import__("math").pi, "e": __import__("math").e,
            }
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


@dataclass
class SearchTool(BaseTool):
    """Web search tool using web search API."""
    
    name: str = "search"
    description: str = "Search the web for information. Input should be a search query."
    
    def execute(self, query: str) -> str:
        """Search for information."""
        try:
            from open_agent.integrations.google import search_web
            results = search_web(query, num_results=5)
            return results
        except ImportError:
            return "Search tool requires google-api-python-client. Install with: pip install google-api-python-client"
        except Exception as e:
            return f"Search error: {str(e)}"


@dataclass
class WikipediaTool(BaseTool):
    """Wikipedia search tool."""
    
    name: str = "wikipedia"
    description: str = "Search Wikipedia for information. Input should be a topic to search."
    
    def execute(self, topic: str) -> str:
        """Search Wikipedia."""
        try:
            import wikipedia
            summary = wikipedia.summary(topic, sentences=3)
            return summary
        except ImportError:
            return "Wikipedia tool requires wikipedia package. Install with: pip install wikipedia"
        except wikipedia.exceptions.DisambiguationError as e:
            return f"Multiple results found: {', '.join(e.options[:5])}"
        except Exception as e:
            return f"Wikipedia error: {str(e)}"


@dataclass
class FileReadTool(BaseTool):
    """Read files from the filesystem."""
    
    name: str = "read_file"
    description: str = "Read contents of a file. Input should be a file path."
    
    def execute(self, file_path: str) -> str:
        """Read a file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


@dataclass
class FileWriteTool(BaseTool):
    """Write files to the filesystem."""
    
    name: str = "write_file"
    description: str = "Write content to a file. Input should be in format: file_path|content"
    
    def execute(self, input_str: str) -> str:
        """Write to a file."""
        try:
            file_path, content = input_str.split("|", 1)
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


@dataclass  
class WebFetchTool(BaseTool):
    """Fetch content from a URL."""
    
    name: str = "fetch_url"
    description: str = "Fetch content from a URL. Input should be a URL."
    
    def execute(self, url: str) -> str:
        """Fetch URL content."""
        try:
            import httpx
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            content = response.text[:5000]
            if len(response.text) > 5000:
                content += "\n... (truncated)"
            return content
        except Exception as e:
            return f"Error fetching URL: {str(e)}"


@dataclass
class PythonREPLTool(BaseTool):
    """Execute Python code in a REPL."""
    
    name: str = "python_repl"
    description: str = "Execute Python code. Input should be Python code to execute."
    
    def execute(self, code: str) -> str:
        """Execute Python code."""
        try:
            import io
            import contextlib
            
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": __builtins__})
            
            result = output.getvalue()
            return result if result else "Code executed successfully (no output)"
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"


@dataclass
class GitHubTool(BaseTool):
    """GitHub operations tool."""
    
    name: str = "github"
    description: str = "Perform GitHub operations. Input should be a JSON command."
    
    def execute(self, command_json: str) -> str:
        """Execute GitHub command."""
        try:
            command = json.loads(command_json)
            action = command.get("action", "info")
            
            if action == "search_repos":
                from open_agent.integrations.github import search_repositories
                query = command.get("query", "")
                return search_repositories(query)
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            return f"GitHub error: {str(e)}"


@dataclass
class JiraTool(BaseTool):
    """Jira integration tool."""
    
    name: str = "jira"
    description: str = "Interact with Jira. Input should be a JSON command."
    
    def execute(self, command_json: str) -> str:
        """Execute Jira command."""
        try:
            command = json.loads(command_json)
            from open_agent.integrations.jira import JiraClient
            
            jira_url = command.get("url", "")
            api_token = command.get("token", "")
            email = command.get("email", "")
            
            if command.get("action") == "create_issue":
                client = JiraClient(jira_url, email, api_token)
                issue = client.create_issue(
                    project=command.get("project"),
                    summary=command.get("summary"),
                    description=command.get("description"),
                    issue_type=command.get("issue_type", "Task")
                )
                return f"Created: {issue}"
            
            return "Jira client initialized"
        except Exception as e:
            return f"Jira error: {str(e)}"


@dataclass
class NotionTool(BaseTool):
    """Notion integration tool."""
    
    name: str = "notion"
    description: str = "Interact with Notion. Input should be a JSON command."
    
    def execute(self, command_json: str) -> str:
        """Execute Notion command."""
        try:
            from open_agent.integrations.notion import NotionClient
            
            command = json.loads(command_json)
            client = NotionClient(command.get("token", ""))
            
            action = command.get("action", "list_pages")
            
            if action == "create_page":
                result = client.create_page(
                    parent_id=command.get("parent_id"),
                    title=command.get("title"),
                    content=command.get("content", "")
                )
                return f"Created page: {result}"
            elif action == "search":
                results = client.search(command.get("query", ""))
                return results
            
            return "Notion client ready"
        except Exception as e:
            return f"Notion error: {str(e)}"


@dataclass
class NewsTool(BaseTool):
    """Get latest news using News API."""
    
    name: str = "news"
    description: str = "Get latest news articles. Input should be a topic or 'latest'."
    
    def execute(self, topic: str = "latest") -> str:
        """Get news."""
        try:
            import httpx
            
            api_key = ""
            url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={api_key}&pageSize=5"
            
            if not api_key:
                return "News API key not configured. Set NEWS_API_KEY in environment."
            
            response = httpx.get(url, timeout=10)
            data = response.json()
            
            articles = data.get("articles", [])
            if not articles:
                return "No news found."
            
            result = "Latest News:\n\n"
            for i, article in enumerate(articles[:5], 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Source: {article['source']['name']}\n"
                result += f"   URL: {article['url']}\n\n"
            
            return result
        except Exception as e:
            return f"News error: {str(e)}"


def get_default_tools() -> List[BaseTool]:
    """Get a list of all default tools."""
    return [
        CalculatorTool(),
        WikipediaTool(),
        WebFetchTool(),
        PythonREPLTool(),
        NewsTool(),
    ]


def get_tools_by_category(category: str) -> List[BaseTool]:
    """Get tools by category."""
    categories = {
        "math": [CalculatorTool()],
        "research": [SearchTool(), WikipediaTool(), NewsTool()],
        "web": [WebFetchTool(), SearchTool()],
        "code": [PythonREPLTool()],
        "files": [FileReadTool(), FileWriteTool()],
        "productivity": [NotionTool(), JiraTool(), GitHubTool()],
    }
    return categories.get(category, [])
