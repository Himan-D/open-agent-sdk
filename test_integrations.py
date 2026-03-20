"""Test all integrations."""

import asyncio
import os

async def test_integrations():
    """Test all integration modules."""
    print("="*60)
    print("OpenAgent - Integration Tests")
    print("="*60)
    
    # Test 1: Google Workspace
    print("\n[1/3] Testing Google Workspace...")
    try:
        from open_agent.integrations.google import (
            GoogleWorkspace,
            GoogleOAuthFlow,
            GoogleOAuthConfig,
            create_google_workspace,
        )
        
        # Create workspace
        workspace = create_google_workspace(
            client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        )
        
        print("✓ Google Workspace imported successfully")
        print(f"  - Authenticated: {workspace.is_authenticated}")
        
        if workspace.is_authenticated:
            print("  - Gmail: available")
            print("  - Calendar: available")
            print("  - Drive: available")
        else:
            print("  ⚠ Not authenticated - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        
    except ImportError as e:
        print(f"⚠ Google libraries not installed: {e}")
        print("  Install with: pip install google-api-python-client google-auth")
    except Exception as e:
        print(f"✗ Google Workspace failed: {e}")

    # Test 2: GitHub
    print("\n[2/3] Testing GitHub...")
    try:
        from open_agent.integrations.github import (
            GitHubClient,
            GitHubConfig,
            create_github_client,
        )
        
        # Create client
        client = create_github_client(
            token=os.environ.get("GITHUB_TOKEN", ""),
            username=os.environ.get("GITHUB_USERNAME", ""),
        )
        
        print("✓ GitHub imported successfully")
        print(f"  - Token set: {'Yes' if client.config.token else 'No'}")
        print(f"  - Username: {client.config.username or 'Not set'}")
        
    except ImportError as e:
        print(f"⚠ PyGithub not installed: {e}")
        print("  Install with: pip install PyGithub")
    except Exception as e:
        print(f"✗ GitHub failed: {e}")

    # Test 3: Notion
    print("\n[3/3] Testing Notion...")
    try:
        from open_agent.integrations.notion import (
            NotionClient,
            NotionConfig,
            create_notion_client,
        )
        
        # Create client
        client = create_notion_client(
            token=os.environ.get("NOTION_TOKEN", ""),
            database_id=os.environ.get("NOTION_DATABASE_ID", ""),
        )
        
        print("✓ Notion imported successfully")
        print(f"  - Token set: {'Yes' if client.config.token else 'No'}")
        print(f"  - Database ID: {client.config.database_id or 'Not set'}")
        
    except ImportError as e:
        print(f"⚠ Notion client not installed: {e}")
        print("  Install with: pip install notion-client")
    except Exception as e:
        print(f"✗ Notion failed: {e}")

    # Summary
    print("\n" + "="*60)
    print("Integration Summary")
    print("="*60)
    print("""
To enable integrations, set these environment variables:

GOOGLE:
  GOOGLE_CLIENT_ID=xxx
  GOOGLE_CLIENT_SECRET=xxx
  
GITHUB:
  GITHUB_TOKEN=ghp_xxx
  GITHUB_USERNAME=your_username
  
NOTION:
  NOTION_TOKEN=secret_xxx
  NOTION_DATABASE_ID=xxx

Then run OAuth flow:
  workspace = create_google_workspace()
  url, state = workspace.get_auth_url()
  # Visit URL, get callback
  workspace.complete_auth(callback_url)
""")

if __name__ == "__main__":
    asyncio.run(test_integrations())
