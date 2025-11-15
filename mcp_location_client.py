#!/usr/bin/env python3
"""
MCP Client for Location Services
This script connects to a public MCP server to get current location information.
"""

import asyncio
import json
from typing import Any, Dict
import httpx


class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session_id = None

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "location-client",
                        "version": "1.0.0"
                    }
                }
            )
            result = response.json()
            print(f"✓ Connected to MCP server: {result.get('serverInfo', {}).get('name', 'Unknown')}")
            return result

    async def list_tools(self) -> list:
        """List available tools from the MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/list",
                json={}
            )
            tools = response.json().get("tools", [])
            print(f"\n✓ Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
            return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool on the MCP server"""
        if arguments is None:
            arguments = {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            return response.json()


async def get_location_via_mcp():
    """
    Get current location using an MCP server.

    Note: This is a demonstration using a hypothetical location MCP server.
    In practice, you would use a real MCP server URL that provides location services.
    """

    # Example MCP server URL (replace with actual public MCP server)
    # For demonstration, we'll show the structure
    mcp_server_url = "http://localhost:3000/mcp"

    print("=" * 60)
    print("MCP Location Client")
    print("=" * 60)

    try:
        # Create MCP client
        client = MCPClient(mcp_server_url)

        # Initialize connection
        print("\n[1] Initializing MCP connection...")
        await client.initialize()

        # List available tools
        print("\n[2] Discovering available tools...")
        tools = await client.list_tools()

        # Call location tool
        print("\n[3] Requesting current location...")
        result = await client.call_tool("get_location")

        # Display results
        print("\n" + "=" * 60)
        print("LOCATION INFORMATION")
        print("=" * 60)

        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                print(item.get("text"))

        return result

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to MCP server")
        print("   Make sure the MCP server is running at:", mcp_server_url)
        print("\nAlternative: Using IP-based location lookup...")
        await get_location_via_ip()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFalling back to IP-based location...")
        await get_location_via_ip()


async def get_location_via_ip():
    """
    Fallback method: Get approximate location using IP geolocation API
    This doesn't use MCP but demonstrates location retrieval
    """
    print("\n" + "=" * 60)
    print("IP-Based Location Lookup (Fallback)")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Using a free IP geolocation service
            response = await client.get("https://ipapi.co/json/")
            data = response.json()

            print(f"\n📍 Location Information:")
            print(f"   IP Address: {data.get('ip', 'Unknown')}")
            print(f"   City: {data.get('city', 'Unknown')}")
            print(f"   Region: {data.get('region', 'Unknown')}")
            print(f"   Country: {data.get('country_name', 'Unknown')} ({data.get('country', 'Unknown')})")
            print(f"   Coordinates: {data.get('latitude', 'Unknown')}, {data.get('longitude', 'Unknown')}")
            print(f"   Timezone: {data.get('timezone', 'Unknown')}")
            print(f"   ISP: {data.get('org', 'Unknown')}")

            return data

    except Exception as e:
        print(f"❌ Error getting location: {e}")


# Alternative: Simple MCP server example for testing
async def run_simple_mcp_server():
    """
    Example of a simple MCP server that could provide location services.
    This would run separately from the client.
    """
    from aiohttp import web

    async def initialize(request):
        data = await request.json()
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "location-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(request):
        return web.json_response({
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get current location based on IP address",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        })

    async def call_tool(request):
        data = await request.json()
        tool_name = data.get("name")

        if tool_name == "get_location":
            # In a real implementation, this would get actual location
            async with httpx.AsyncClient() as client:
                response = await client.get("https://ipapi.co/json/")
                location_data = response.json()

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"Location: {location_data.get('city')}, {location_data.get('country_name')}\n"
                               f"Coordinates: {location_data.get('latitude')}, {location_data.get('longitude')}"
                    }
                ]
            })

        return web.json_response({"error": "Unknown tool"}, status=400)

    app = web.Application()
    app.router.add_post('/mcp/initialize', initialize)
    app.router.add_post('/mcp/tools/list', list_tools)
    app.router.add_post('/mcp/tools/call', call_tool)

    print("Starting MCP server on http://localhost:3000")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()


if __name__ == "__main__":
    print("\n🌍 MCP Location Service Client\n")
    print("This script demonstrates accessing location via MCP protocol.")
    print("If no MCP server is available, it falls back to IP geolocation.\n")

    # Run the client
    asyncio.run(get_location_via_mcp())
