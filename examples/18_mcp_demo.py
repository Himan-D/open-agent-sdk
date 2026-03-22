#!/usr/bin/env python3
"""MCP (Model Context Protocol) Demo for SmithAI.

This demo showcases:
1. MCP Client - Connect to external MCP servers
2. MCP Server - Expose SmithAI tools as MCP server
3. Google Sheets integration (as MCP server)
4. Multi-server management

Requirements:
    pip install mcp anthropic gspread google-auth
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smith_ai.mcp import (
    MCPClient,
    MCPServer,
    GoogleSheetsMCPServer,
    MultiMCPServerManager,
    SmithAIMCPClient,
)


async def demo_mcp_client():
    """Demo 1: MCP Client - Connect to an MCP server."""
    print("\n" + "="*70)
    print("DEMO 1: MCP Client - Connect to external MCP server")
    print("="*70)
    
    client = MCPClient(verbose=True)
    
    # Create a simple MCP server script for testing
    test_server = """
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TestServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two numbers.\"\"\"
    return a * b

@mcp.tool()
def greet(name: str) -> str:
    \"\"\"Greet someone.\"\"\"
    return f"Hello, {name}!"

@mcp.resource("test://greeting")
def greeting() -> str:
    return "Welcome to SmithAI MCP Demo!"

if __name__ == "__main__":
    mcp.run()
"""
    
    # Write test server to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_server)
        server_path = f.name
    
    print(f"\n[1] Created test MCP server at: {server_path}")
    
    # Connect to the test server
    print("\n[2] Connecting to test MCP server...")
    success = await client.connect_to_server(server_path, "test-server")
    print(f"    Connected: {success}")
    
    # List available tools
    print("\n[3] Available tools:")
    tools = await client.list_tools()
    for tool in tools:
        print(f"    - {tool['name']}: {tool['description'][:50]}...")
    
    # Call a tool
    print("\n[4] Calling 'add' tool:")
    result = await client.call_tool("add", {"a": 10, "b": 20})
    print(f"    Result: {result}")
    
    print("\n[5] Calling 'greet' tool:")
    result = await client.call_tool("greet", {"name": "SmithAI"})
    print(f"    Result: {result}")
    
    # Read a resource
    print("\n[6] Reading resource 'test://greeting':")
    resource = await client.read_resource("test://greeting")
    print(f"    Resource: {resource}")
    
    # Cleanup
    await client.disconnect("test-server")
    os.unlink(server_path)
    
    return True


async def demo_mcp_server():
    """Demo 2: MCP Server - Expose SmithAI tools as MCP server."""
    print("\n" + "="*70)
    print("DEMO 2: MCP Server - Expose SmithAI tools")
    print("="*70)
    
    server = MCPServer(name="SmithAI Tools", verbose=True)
    
    @server.tool()
    def calculate(expression: str) -> str:
        """Evaluate a mathematical expression.
        
        Args:
            expression: A mathematical expression like '2 + 2' or '10 * 5'
        """
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    
    @server.tool()
    def reverse_text(text: str) -> str:
        """Reverse a string.
        
        Args:
            text: Text to reverse
        """
        return text[::-1]
    
    @server.tool()
    def word_count(text: str) -> str:
        """Count words and characters in text.
        
        Args:
            text: Text to analyze
        """
        words = text.split()
        return json.dumps({
            "words": len(words),
            "characters": len(text),
            "characters_no_space": len(text.replace(" ", ""))
        })
    
    @server.resource("smithai://status")
    def get_status() -> str:
        """Get SmithAI status."""
        return json.dumps({
            "status": "running",
            "version": "4.1.0",
            "tools": ["calculate", "reverse_text", "word_count"]
        })
    
    print("\n[1] Created SmithAI MCP Server with tools:")
    manifest = server.get_manifest()
    for tool in manifest["tools"]:
        print(f"    - {tool['name']}")
    
    print(f"\n[2] Server manifest:")
    print(json.dumps(manifest, indent=2))
    
    print("\n[3] To run this server:")
    print("    # Option 1: Direct run")
    print("    python -m smith_ai.mcp --type custom")
    print()
    print("    # Option 2: Connect from Claude Desktop")
    print("    Add to ~/.claude.json:")
    print(json.dumps({
        "mcpServers": {
            "smithai-tools": {
                "command": "python",
                "args": ["-m", "smith_ai.mcp"]
            }
        }
    }, indent=4))
    
    return True


async def demo_google_sheets():
    """Demo 3: Google Sheets MCP Server."""
    print("\n" + "="*70)
    print("DEMO 3: Google Sheets MCP Server")
    print("="*70)
    
    print("\n[1] Google Sheets MCP Server creates these tools:")
    print("    - read_sheet: Read data from a Google Sheet")
    print("    - write_sheet: Write data to a Google Sheet")
    print("    - append_row: Append a row to a sheet")
    print("    - update_cell: Update a specific cell")
    print("    - create_spreadsheet: Create a new spreadsheet")
    print("    - list_spreadsheets: List all accessible spreadsheets")
    
    print("\n[2] Google Sheets MCP Server resources:")
    print("    - googlesheets://spreadsheet/{id}: Get spreadsheet data")
    print("    - googlesheets://{spreadsheet_id}/{range}: Get specific range")
    
    print("\n[3] Usage examples:")
    
    print("""
    # As MCP Server (expose to Claude Desktop)
    server = GoogleSheetsMCPServer(
        credentials_path="path/to/credentials.json",
        spreadsheet_id="your_spreadsheet_id"
    )
    server.run()  # Runs as stdio server
    
    # From Claude Desktop, add to config:
    {
        "mcpServers": {
            "google-sheets": {
                "command": "python",
                "args": ["-m", "smith_ai.mcp", "--type", "google-sheets", 
                         "--credentials", "path/to/creds.json",
                         "--sheets-id", "your_spreadsheet_id"]
            }
        }
    }
    """)
    
    print("\n[4] MCP Tool calls example:")
    print("""
    # Read sheet data
    result = await client.call_tool("read_sheet", {
        "range_name": "Sheet1!A1:D10",
        "spreadsheet_id": "your_spreadsheet_id"
    })
    
    # Write data
    result = await client.call_tool("write_sheet", {
        "range_name": "Sheet1!A1",
        "values": [["Name", "Age", "City"], ["John", 30, "NYC"]],
        "spreadsheet_id": "your_spreadsheet_id"
    })
    
    # Append row
    result = await client.call_tool("append_row", {
        "values": ["New Entry", 25, "LA"],
        "sheet_name": "Sheet1"
    })
    """)
    
    return True


async def demo_multi_server():
    """Demo 4: Multi-Server Manager."""
    print("\n" + "="*70)
    print("DEMO 4: Multi-Server Manager")
    print("="*70)
    
    manager = MultiMCPServerManager(verbose=True)
    
    print("\n[1] MultiServerManager allows connecting to multiple MCP servers")
    print("    and calling tools from any of them seamlessly.")
    
    print("\n[2] Usage:")
    print("""
    manager = MultiMCPServerManager()
    
    # Connect to multiple servers
    await manager.connect("github", "path/to/github_server.py")
    await manager.connect("filesystem", "path/to/fs_server.py")
    await manager.connect("database", "path/to/db_server.py")
    
    # List all available tools
    all_tools = await manager.list_all_tools()
    
    # Call tool on specific server
    result = await manager.call_tool("create_issue", {...}, "github")
    
    # Or auto-route to any server that has it
    result = await manager.call_any_server("read_file", {...})
    """)
    
    print("\n[3] Connected servers:")
    print(f"    {manager.connected_servers()}")
    
    return True


async def demo_smithai_integration():
    """Demo 5: SmithAI MCP Integration."""
    print("\n" + "="*70)
    print("DEMO 5: SmithAI Agent with MCP Integration")
    print("="*70)
    
    print("\n[1] SmithAIMCPClient combines:")
    print("    - SmithAI's agentic capabilities")
    print("    - MCP server access")
    print("    - Automatic tool discovery")
    
    print("\n[2] Usage:")
    print("""
    agent = SmithAIMCPClient()
    
    # Connect to MCP servers
    await agent.connect_mcp_server("github", "path/to/github_server.py")
    await agent.connect_mcp_server("sheets", "path/to/sheets_server.py")
    
    # Use MCP tools in agent reasoning
    response = await agent.run(
        "Create a GitHub issue and add it to our tracking spreadsheet"
    )
    
    # Or call MCP tools directly
    result = await agent.call_mcp_tool("create_issue", {
        "repo": "owner/repo",
        "title": "Bug report",
        "body": "Found an issue..."
    })
    
    # List available MCP tools
    tools = agent.list_mcp_tools()
    """)
    
    return True


async def main():
    """Run all MCP demos."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀 SmithAI MCP (Model Context Protocol) Demo                   ║
║                                                                  ║
║   MCP enables:                                                    ║
║   ✓ Connect to external MCP servers (like Claude Desktop)        ║
║   ✓ Expose SmithAI tools as MCP server                          ║
║   ✓ Google Sheets integration                                    ║
║   ✓ Multi-server management                                      ║
║   ✓ Universal tool discovery                                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    demos = [
        ("MCP Client", demo_mcp_client),
        ("MCP Server", demo_mcp_server),
        ("Google Sheets", demo_google_sheets),
        ("Multi-Server Manager", demo_multi_server),
        ("SmithAI Integration", demo_smithai_integration),
    ]
    
    passed = 0
    for name, demo in demos:
        try:
            result = await demo()
            if result:
                passed += 1
                print(f"\n✅ {name} Demo PASSED")
        except Exception as e:
            print(f"\n❌ {name} Demo FAILED: {e}")
    
    print("\n" + "="*70)
    print(f"FINAL RESULT: {passed}/{len(demos)} demos passed")
    print("="*70)
    
    return passed == len(demos)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
