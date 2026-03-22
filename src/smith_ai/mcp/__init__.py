"""MCP (Model Context Protocol) Integration for SmithAI.

This module provides:
1. MCP Client - Connect to any MCP server (like Claude Desktop)
2. MCP Server - Expose SmithAI tools as MCP server (like Claude Work)
3. Google Sheets integration
4. Multi-server management

Architecture:
- SmithAI Agent <-> MCP Client <-> External MCP Servers
- External Tools <-> MCP Server <-> Claude Desktop/Code

Usage:
    # As MCP Client (connect to external servers)
    client = MCPClient()
    await client.connect_to_server("path/to/server.py")
    tools = await client.list_tools()
    result = await client.call_tool("tool_name", {"arg": "value"})

    # As MCP Server (expose SmithAI tools)
    server = MCPServer(name="SmithAI")
    @server.tool()
    def my_tool(arg: str) -> str:
        return f"Processed: {arg}"
    server.run()
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol
from enum import Enum

import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
    FastMCP = None

try:
    import gspread
    from google.oauth2 import service_account
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    gspread = None
    service_account = None


# =============================================================================
# MCP CLIENT - Connect to external MCP servers
# =============================================================================

class MCPClient:
    """MCP Client that connects to external MCP servers.
    
    This allows SmithAI to use tools from any MCP-compatible server,
    just like Claude Desktop or Claude Code.
    
    Example:
        client = MCPClient()
        await client.connect_to_server("path/to/server.py")
        tools = await client.list_tools()
        result = await client.call_tool("tool_name", {"arg": "value"})
    """
    
    def __init__(self, verbose: bool = True):
        if not MCP_AVAILABLE:
            raise ImportError("MCP not installed. Run: pip install mcp")
        
        self.verbose = verbose
        self.sessions: Dict[str, Any] = {}
        self._connected_servers: Dict[str, Any] = {}
        
    async def connect_to_server(
        self,
        server_path: str,
        server_name: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server.
        
        Args:
            server_path: Path to the server script (.py or .js)
            server_name: Optional name for this server connection
            env: Optional environment variables
            
        Returns:
            True if connected successfully
        """
        server_name = server_name or Path(server_path).stem
        
        if server_name in self._connected_servers:
            if self.verbose:
                print(f"[MCP] Already connected to {server_name}")
            return True
        
        is_python = server_path.endswith('.py')
        is_js = server_path.endswith('.js')
        
        if not (is_python or is_js):
            raise ValueError("Server script must be .py or .js")
        
        command = sys.executable if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_path],
            env=env,
        )
        
        try:
            if self.verbose:
                print(f"[MCP] Connecting to {server_name}...")
            
            read, write = await stdio_client(server_params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            
            self._connected_servers[server_name] = {
                "session": session,
                "read": read,
                "write": write,
                "path": server_path,
            }
            
            if self.verbose:
                tools = await session.list_tools()
                print(f"[MCP] Connected to {server_name} with {len(tools.tools)} tools")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"[MCP] Failed to connect to {server_name}: {e}")
            return False
    
    async def disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        if server_name not in self._connected_servers:
            return False
        
        try:
            server_info = self._connected_servers[server_name]
            await server_info["session"].__aexit__(None, None, None)
            del self._connected_servers[server_name]
            
            if self.verbose:
                print(f"[MCP] Disconnected from {server_name}")
            return True
        except Exception as e:
            if self.verbose:
                print(f"[MCP] Error disconnecting from {server_name}: {e}")
            return False
    
    async def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available tools from MCP server(s).
        
        Args:
            server_name: Optional specific server. If None, lists all tools.
            
        Returns:
            List of tool definitions
        """
        if server_name:
            if server_name not in self._connected_servers:
                return []
            session = self._connected_servers[server_name]["session"]
            result = await session.list_tools()
            return [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                    "server": server_name,
                }
                for t in result.tools
            ]
        
        all_tools = []
        for name, info in self._connected_servers.items():
            try:
                tools = await info["session"].list_tools()
                for t in tools.tools:
                    all_tools.append({
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.inputSchema,
                        "server": name,
                    })
            except:
                pass
        
        return all_tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call a tool on an MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as dict
            server_name: Optional specific server. Auto-detects if not provided.
            
        Returns:
            Tool execution result
        """
        if server_name:
            if server_name not in self._connected_servers:
                return {"error": f"Not connected to {server_name}"}
            session = self._connected_servers[server_name]["session"]
            result = await session.call_tool(tool_name, arguments)
            return self._parse_result(result)
        
        # Auto-detect server for tool
        for name, info in self._connected_servers.items():
            try:
                session = info["session"]
                result = await session.call_tool(tool_name, arguments)
                return self._parse_result(result)
            except:
                continue
        
        return {"error": f"Tool {tool_name} not found on any connected server"}
    
    def _parse_result(self, result: Any) -> Dict[str, Any]:
        """Parse MCP tool result."""
        if hasattr(result, 'content'):
            content = []
            for item in result.content:
                if hasattr(item, 'text'):
                    try:
                        content.append(json.loads(item.text))
                    except:
                        content.append(item.text)
                elif hasattr(item, 'data'):
                    content.append(item.data)
            return {"content": content, "isError": getattr(result, 'isError', False)}
        return {"content": str(result)}
    
    async def list_resources(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available resources from MCP server(s)."""
        all_resources = []
        
        servers = [server_name] if server_name else self._connected_servers.keys()
        
        for name in servers:
            if name not in self._connected_servers:
                continue
            try:
                session = self._connected_servers[name]["session"]
                result = await session.list_resources()
                for r in result.resources:
                    all_resources.append({
                        "uri": r.uri,
                        "name": r.name,
                        "description": r.description,
                        "mime_type": r.mimeType,
                        "server": name,
                    })
            except:
                pass
        
        return all_resources
    
    async def read_resource(self, uri: str) -> Optional[str]:
        """Read a resource by URI."""
        for name, info in self._connected_servers.items():
            try:
                result = await info["session"].read_resource(uri)
                if hasattr(result, 'contents'):
                    for item in result.contents:
                        if hasattr(item, 'text'):
                            return item.text
            except:
                continue
        return None
    
    def connected_servers(self) -> List[str]:
        """Get list of connected server names."""
        return list(self._connected_servers.keys())
    
    async def close_all(self):
        """Close all connections."""
        for name in list(self._connected_servers.keys()):
            await self.disconnect(name)


# =============================================================================
# MCP SERVER - Expose SmithAI tools as MCP server
# =============================================================================

class MCPServer:
    """MCP Server that exposes SmithAI tools.
    
    This allows external clients (Claude Desktop, Claude Code, etc.)
    to use SmithAI tools via MCP protocol.
    
    Example:
        server = MCPServer(name="SmithAI Tools")
        
        @server.tool()
        def calculate(expression: str) -> str:
            return str(eval(expression))
        
        @server.resource("smithai://status")
        def get_status() -> str:
            return json.dumps({"status": "running"})
        
        server.run()  # Runs as stdio server
    """
    
    def __init__(self, name: str = "SmithAI", verbose: bool = True):
        if not MCP_AVAILABLE:
            raise ImportError("MCP not installed. Run: pip install mcp")
        
        self.name = name
        self.verbose = verbose
        self._mcp = FastMCP(name)
        self._tools: Dict[str, Callable] = {}
        self._resources: Dict[str, Callable] = {}
        self._prompts: Dict[str, Callable] = {}
        
    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a tool.
        
        Args:
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""
            
            self._tools[tool_name] = func
            
            @self._mcp.tool(name=tool_name)
            async def wrapped_tool(**kwargs):
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return str(result) if result is not None else ""
            
            if self.verbose:
                print(f"[MCP Server] Registered tool: {tool_name}")
            
            return func
        return decorator
    
    def resource(self, uri_template: str, name: Optional[str] = None):
        """Decorator to register a resource.
        
        Args:
            uri_template: URI template like "smithai://{resource_name}"
            name: Optional resource name
        """
        def decorator(func: Callable) -> Callable:
            self._resources[uri_template] = func
            
            @self._mcp.resource(uri_template)
            async def wrapped_resource(*args, **kwargs):
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return str(result) if result is not None else ""
            
            if self.verbose:
                print(f"[MCP Server] Registered resource: {uri_template}")
            
            return func
        return decorator
    
    def prompt(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a prompt template.
        
        Args:
            name: Prompt name (defaults to function name)
            description: Prompt description
        """
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            prompt_desc = description or func.__doc__ or ""
            
            self._prompts[prompt_name] = func
            
            @self._mcp.prompt(name=prompt_name)
            async def wrapped_prompt(*args, **kwargs):
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return str(result) if result is not None else ""
            
            if self.verbose:
                print(f"[MCP Server] Registered prompt: {prompt_name}")
            
            return func
        return decorator
    
    def register_tool(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """Register a tool function directly."""
        return self.tool(name=name, description=description)(func)
    
    def run(self, transport: str = "stdio", host: str = "localhost", port: int = 8080):
        """Run the MCP server.
        
        Args:
            transport: "stdio" for local, "streamable-http" for network
            host: Host for HTTP transport
            port: Port for HTTP transport
        """
        if self.verbose:
            print(f"[MCP Server] Starting {self.name} on {transport}")
            print(f"[MCP Server] Tools: {list(self._tools.keys())}")
            print(f"[MCP Server] Resources: {list(self._resources.keys())}")
        
        if transport == "streamable-http":
            self._mcp.run(transport=transport, host=host, port=port)
        else:
            self._mcp.run(transport="stdio")
    
    def get_manifest(self) -> Dict[str, Any]:
        """Get server manifest for client registration."""
        return {
            "name": self.name,
            "tools": [
                {
                    "name": name,
                    "description": func.__doc__ or "",
                }
                for name, func in self._tools.items()
            ],
            "resources": list(self._resources.keys()),
            "prompts": list(self._prompts.keys()),
        }


# =============================================================================
# GOOGLE SHEETS MCP SERVER
# =============================================================================

class GoogleSheetsMCPServer:
    """MCP Server for Google Sheets operations.
    
    This exposes Google Sheets as an MCP server that can be used by
    any MCP-compatible client (Claude Desktop, Claude Code, SmithAI).
    
    Tools:
    - read_sheet: Read data from a sheet
    - write_sheet: Write data to a sheet
    - append_row: Append a row to a sheet
    - update_cell: Update a specific cell
    - create_spreadsheet: Create a new spreadsheet
    - list_spreadsheets: List available spreadsheets
    
    Requires:
        pip install gspread google-auth google-api-python-client
        Set GOOGLE_APPLICATION_CREDENTIALS or use OAuth
    """
    
    def __init__(self, credentials_path: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID")
        self._mcp = None
        self._gsheets = None
        self._setup_mcp()
    
    def _setup_mcp(self):
        """Setup MCP server with Google Sheets tools."""
        if not MCP_AVAILABLE:
            print("[Google Sheets MCP] MCP not available, using mock mode")
            return
        
        self._mcp = FastMCP("Google Sheets")
        
        @self._mcp.tool()
        async def read_sheet(
            range_name: str = "Sheet1!A1:Z1000",
            spreadsheet_id: Optional[str] = None
        ) -> str:
            """Read data from a Google Sheet.
            
            Args:
                range_name: The range to read (e.g., 'Sheet1!A1:D10')
                spreadsheet_id: Optional spreadsheet ID (uses default if not provided)
            """
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                ss_id = spreadsheet_id or self.spreadsheet_id
                if not ss_id:
                    return json.dumps({"error": "No spreadsheet ID provided"})
                
                sheet = gs.open_by_key(ss_id)
                worksheet = sheet.sheet1
                values = worksheet.get(range_name)
                return json.dumps({"data": values, "range": range_name})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.tool()
        async def write_sheet(
            range_name: str,
            values: List[List[Any]],
            spreadsheet_id: Optional[str] = None
        ) -> str:
            """Write data to a Google Sheet.
            
            Args:
                range_name: The range to write to (e.g., 'Sheet1!A1')
                values: 2D array of values to write
                spreadsheet_id: Optional spreadsheet ID
            """
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                ss_id = spreadsheet_id or self.spreadsheet_id
                if not ss_id:
                    return json.dumps({"error": "No spreadsheet ID provided"})
                
                sheet = gs.open_by_key(ss_id)
                worksheet = sheet.sheet1
                worksheet.update(range_name, values)
                return json.dumps({"success": True, "range": range_name})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.tool()
        async def append_row(
            values: List[Any],
            sheet_name: str = "Sheet1",
            spreadsheet_id: Optional[str] = None
        ) -> str:
            """Append a row to a sheet.
            
            Args:
                values: List of values for the new row
                sheet_name: Name of the sheet (default: Sheet1)
                spreadsheet_id: Optional spreadsheet ID
            """
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                ss_id = spreadsheet_id or self.spreadsheet_id
                if not ss_id:
                    return json.dumps({"error": "No spreadsheet ID provided"})
                
                sheet = gs.open_by_key(ss_id)
                worksheet = sheet.worksheet(sheet_name)
                worksheet.append_row(values)
                return json.dumps({"success": True, "values": values})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.tool()
        async def update_cell(
            cell: str,
            value: Any,
            spreadsheet_id: Optional[str] = None
        ) -> str:
            """Update a specific cell.
            
            Args:
                cell: Cell reference (e.g., 'A1')
                value: Value to set
                spreadsheet_id: Optional spreadsheet ID
            """
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                ss_id = spreadsheet_id or self.spreadsheet_id
                if not ss_id:
                    return json.dumps({"error": "No spreadsheet ID provided"})
                
                sheet = gs.open_by_key(ss_id)
                worksheet = sheet.sheet1
                worksheet.update(cell, value)
                return json.dumps({"success": True, "cell": cell, "value": value})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.tool()
        async def create_spreadsheet(
            title: str,
            sheet_name: str = "Sheet1"
        ) -> str:
            """Create a new Google Spreadsheet.
            
            Args:
                title: Title for the new spreadsheet
                sheet_name: Name for the first sheet
            """
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                spreadsheet = gs.create(title)
                if sheet_name != "Sheet1":
                    spreadsheet.add_worksheet(sheet_name, rows=1000, cols=26)
                return json.dumps({
                    "success": True,
                    "spreadsheet_id": spreadsheet.id,
                    "title": title
                })
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.tool()
        async def list_spreadsheets() -> str:
            """List all accessible spreadsheets."""
            if not self._gsheets:
                return json.dumps({"error": "Google Sheets not authenticated"})
            
            try:
                gs = self._get_gsheets()
                spreadsheets = gs.list_spreadsheets()
                return json.dumps({"spreadsheets": spreadsheets})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self._mcp.resource("googlesheets://spreadsheet/{id}")
        async def get_spreadsheet(id: str) -> str:
            """Get spreadsheet data as resource."""
            return await read_sheet("Sheet1!A1:Z1000", id)
        
        @self._mcp.resource("googlesheets://{spreadsheet_id}/{range}")
        async def get_range(spreadsheet_id: str, range: str) -> str:
            """Get specific range as resource."""
            return await read_sheet(range, spreadsheet_id)
    
    def _get_gsheets(self):
        """Get authenticated gspread client."""
        if self._gsheets:
            return self._gsheets
        
        try:
            import gspread
            from google.oauth2 import service_account
            
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=scope
                )
            else:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_INFO", "{}")),
                    scopes=scope
                )
            
            self._gsheets = gspread.authorize(credentials)
            print("[Google Sheets MCP] Authenticated successfully")
            return self._gsheets
            
        except ImportError:
            print("[Google Sheets MCP] gspread not installed. Run: pip install gspread google-auth")
            return None
        except Exception as e:
            print(f"[Google Sheets MCP] Authentication failed: {e}")
            return None
    
    def authenticate_with_oauth(self, client_secret_path: str):
        """Authenticate using OAuth2 (for desktop apps).
        
        Args:
            client_secret_path: Path to OAuth client secret JSON
        """
        try:
            import gspread
            from google.oauth2 import credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.file"
            ]
            
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
            self._gsheets = gspread.authorize(creds)
            print("[Google Sheets MCP] OAuth authentication successful")
            
        except Exception as e:
            print(f"[Google Sheets MCP] OAuth failed: {e}")
    
    def authenticate_with_token(self, token_path: str = "token.json"):
        """Authenticate using saved token file."""
        try:
            import gspread
            from google.oauth2 import credentials
            import pickle
            
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            
            self._gsheets = gspread.authorize(creds)
            print("[Google Sheets MCP] Token authentication successful")
            
        except Exception as e:
            print(f"[Google Sheets MCP] Token auth failed: {e}")
    
    def run(self, transport: str = "stdio"):
        """Run the Google Sheets MCP server."""
        if not self._mcp:
            print("[Google Sheets MCP] MCP not available")
            return
        
        print(f"[Google Sheets MCP] Starting server on {transport}")
        self._mcp.run(transport=transport)


# =============================================================================
# MULTI-SERVER MANAGER
# =============================================================================

class MultiMCPServerManager:
    """Manage multiple MCP server connections.
    
    Example:
        manager = MultiMCPServerManager()
        
        # Connect to multiple servers
        await manager.connect("github", "path/to/github_server.py")
        await manager.connect("filesystem", "path/to/fs_server.py")
        
        # Use any tool - auto-routes to correct server
        result = await manager.call_tool("github", "create_issue", {...})
        
        # List all available tools
        all_tools = await manager.list_all_tools()
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._client = MCPClient(verbose=verbose)
        self._servers: Dict[str, Dict[str, Any]] = {}
    
    async def connect(
        self,
        server_name: str,
        server_path: str,
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server."""
        success = await self._client.connect_to_server(
            server_path, server_name, env
        )
        if success:
            self._servers[server_name] = {"path": server_path}
        return success
    
    async def disconnect(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        success = await self._client.disconnect(server_name)
        if success and server_name in self._servers:
            del self._servers[server_name]
        return success
    
    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """List tools from all connected servers."""
        return await self._client.list_tools()
    
    async def list_server_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List tools from a specific server."""
        return await self._client.list_tools(server_name)
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call a tool on a server."""
        return await self._client.call_tool(tool_name, arguments, server_name)
    
    async def call_any_server(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on any server that has it (auto-discovery)."""
        return await self._client.call_tool(tool_name, arguments)
    
    def connected_servers(self) -> List[str]:
        """Get list of connected servers."""
        return self._client.connected_servers()
    
    async def close_all(self):
        """Close all connections."""
        await self._client.close_all()


# =============================================================================
# SMITHAI MCP INTEGRATION
# =============================================================================

class SmithAIMCPClient:
    """SmithAI agent with MCP client capabilities.
    
    This combines SmithAI's agentic capabilities with MCP server access,
    allowing the agent to use tools from any MCP server.
    
    Example:
        agent = SmithAIMCPClient()
        await agent.connect_mcp_server("github_server.py")
        
        # Use MCP tools in agent reasoning
        response = await agent.run("Use the GitHub MCP server to create an issue")
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.mcp_manager = MultiMCPServerManager(verbose=verbose)
        
        # Cache of MCP tools as SmithAI tools
        self._mcp_tools: Dict[str, Callable] = {}
    
    async def connect_mcp_server(
        self,
        server_name: str,
        server_path: str,
        env: Optional[Dict[str, str]] = None
    ) -> bool:
        """Connect to an MCP server."""
        success = await self.mcp_manager.connect(server_name, server_path, env)
        if success:
            await self._sync_tools()
        return success
    
    async def _sync_tools(self):
        """Sync MCP server tools as callable functions."""
        tools = await self.mcp_manager.list_all_tools()
        for tool in tools:
            tool_name = tool["name"]
            self._mcp_tools[tool_name] = self._create_tool_wrapper(tool)
            
            if self.verbose:
                print(f"[SmithAI MCP] Available tool: {tool_name} ({tool.get('server', 'unknown')})")
    
    def _create_tool_wrapper(self, tool_def: Dict[str, Any]) -> Callable:
        """Create a callable wrapper for an MCP tool."""
        async def wrapper(**kwargs):
            result = await self.mcp_manager.call_tool(
                tool_def["name"],
                kwargs,
                tool_def.get("server")
            )
            return result
        
        wrapper.__name__ = tool_def["name"]
        wrapper.__doc__ = tool_def.get("description", "")
        return wrapper
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an MCP tool directly."""
        return await self.mcp_manager.call_any_server(tool_name, arguments)
    
    def get_mcp_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a cached MCP tool callable."""
        return self._mcp_tools.get(tool_name)
    
    def list_mcp_tools(self) -> List[str]:
        """List all available MCP tool names."""
        return list(self._mcp_tools.keys())
    
    async def close(self):
        """Close all MCP connections."""
        await self.mcp_manager.close_all()


# =============================================================================
# CLI FOR MCP SERVERS
# =============================================================================

def create_mcp_server_cli():
    """Create CLI for running MCP servers."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmithAI MCP Server")
    parser.add_argument("--name", default="SmithAI", help="Server name")
    parser.add_argument("--type", choices=["google-sheets", "custom"], default="custom",
                        help="Server type")
    parser.add_argument("--sheets-id", help="Google Sheets spreadsheet ID")
    parser.add_argument("--credentials", help="Path to Google credentials JSON")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio",
                        help="Transport type")
    parser.add_argument("--host", default="localhost", help="Host for HTTP transport")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP transport")
    
    return parser


def main():
    """Main entry point for MCP server CLI."""
    parser = create_mcp_server_cli()
    args = parser.parse_args()
    
    if args.type == "google-sheets":
        server = GoogleSheetsMCPServer(
            credentials_path=args.credentials,
            spreadsheet_id=args.sheets_id
        )
        server.run(transport=args.transport)
    else:
        print("Custom server not implemented. Use --type google-sheets")


if __name__ == "__main__":
    main()
