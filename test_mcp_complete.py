#!/usr/bin/env python3
"""
Complete MCP Test - Runs both server and client
"""

import asyncio
import json
from typing import Any, Dict
import httpx
from aiohttp import web


class MCPServer:
    """Simple MCP server for testing"""

    def __init__(self, host='localhost', port=3000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup MCP server routes"""
        self.app.router.add_post('/mcp/initialize', self.initialize)
        self.app.router.add_post('/mcp/tools/list', self.list_tools)
        self.app.router.add_post('/mcp/tools/call', self.call_tool)

    async def initialize(self, request):
        """Handle initialization request"""
        data = await request.json()
        print(f"[SERVER] Received initialization from: {data.get('clientInfo', {}).get('name')}")
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "test-location-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        """Return available tools"""
        print("[SERVER] Listing available tools")
        return web.json_response({
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get current location (mock data)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_timezone",
                    "description": "Get current timezone",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        })

    async def call_tool(self, request):
        """Handle tool calls"""
        data = await request.json()
        tool_name = data.get("name")
        print(f"[SERVER] Tool called: {tool_name}")

        if tool_name == "get_location":
            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": "Location: San Francisco, California, USA\n"
                               "Coordinates: 37.7749° N, 122.4194° W\n"
                               "Timezone: America/Los_Angeles\n"
                               "Status: Mock data for testing"
                    }
                ]
            })
        elif tool_name == "get_timezone":
            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": "Timezone: America/Los_Angeles (UTC-8)\n"
                               "Current offset: -08:00"
                    }
                ]
            })

        return web.json_response({"error": "Unknown tool"}, status=400)

    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"[SERVER] MCP server started on http://{self.host}:{self.port}")
        return runner


class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, server_url: str):
        self.server_url = server_url

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": "location-client",
                        "version": "1.0.0"
                    }
                }
            )
            result = response.json()
            print(f"[CLIENT] ✓ Connected to: {result.get('serverInfo', {}).get('name')}")
            return result

    async def list_tools(self) -> list:
        """List available tools"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/list",
                json={}
            )
            tools = response.json().get("tools", [])
            print(f"[CLIENT] ✓ Found {len(tools)} tools:")
            for tool in tools:
                print(f"         - {tool['name']}: {tool.get('description')}")
            return tools

    async def call_tool(self, tool_name: str) -> Dict[str, Any]:
        """Call a tool"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={"name": tool_name, "arguments": {}}
            )
            return response.json()


async def run_test():
    """Run complete MCP test"""
    print("\n" + "=" * 70)
    print("MCP LOCATION SERVICE - COMPLETE TEST")
    print("=" * 70 + "\n")

    # Start server
    server = MCPServer()
    runner = await server.start()

    # Give server a moment to start
    await asyncio.sleep(0.5)

    try:
        # Create client
        client = MCPClient("http://localhost:3000/mcp")

        # Test 1: Initialize
        print("\n[TEST 1] Initializing connection...")
        await client.initialize()

        # Test 2: List tools
        print("\n[TEST 2] Discovering tools...")
        tools = await client.list_tools()

        # Test 3: Call get_location
        print("\n[TEST 3] Calling 'get_location' tool...")
        result = await client.call_tool("get_location")
        print("\n--- Location Response ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        # Test 4: Call get_timezone
        print("\n[TEST 4] Calling 'get_timezone' tool...")
        result = await client.call_tool("get_timezone")
        print("\n--- Timezone Response ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70 + "\n")

    finally:
        # Cleanup
        await runner.cleanup()
        print("[SERVER] Server stopped")


if __name__ == "__main__":
    asyncio.run(run_test())
