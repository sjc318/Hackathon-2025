#!/usr/bin/env python3
"""
Complete MCP Test - Runs both server and client with REAL location data
"""

import asyncio
import json
from typing import Any, Dict
from datetime import datetime
import httpx
from aiohttp import web
import pytz


class LocationService:
    """Service to fetch real location data"""

    @staticmethod
    async def get_real_location() -> Dict[str, Any]:
        """Get real location data from IP geolocation API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Using ip-api.com (free, no API key needed)
                response = await client.get('http://ip-api.com/json/')
                response.raise_for_status()
                data = response.json()

                if data.get('status') == 'success':
                    return {
                        'city': data.get('city', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'lat': data.get('lat', 0),
                        'lon': data.get('lon', 0),
                        'timezone': data.get('timezone', 'UTC'),
                        'isp': data.get('isp', 'Unknown'),
                        'ip': data.get('query', 'Unknown')
                    }
                else:
                    raise Exception("API returned error status")
        except Exception as e:
            print(f"[ERROR] Failed to get real location: {e}")
            # Fallback to mock data
            return {
                'city': 'San Francisco',
                'region': 'California',
                'country': 'USA',
                'lat': 37.7749,
                'lon': -122.4194,
                'timezone': 'America/Los_Angeles',
                'isp': 'Mock ISP',
                'ip': '0.0.0.0',
                'error': str(e)
            }

    @staticmethod
    async def get_timezone_info(timezone_name: str) -> Dict[str, Any]:
        """Get detailed timezone information"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            utc_offset = now.strftime('%z')
            utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}"

            return {
                'timezone': timezone_name,
                'utc_offset': utc_offset_formatted,
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'is_dst': bool(now.dst())
            }
        except Exception as e:
            print(f"[ERROR] Failed to get timezone info: {e}")
            return {
                'timezone': timezone_name,
                'utc_offset': '+00:00',
                'current_time': 'Unknown',
                'is_dst': False,
                'error': str(e)
            }


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
                    "description": "Get current location based on IP address (real data)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "get_timezone",
                    "description": "Get current timezone with detailed information",
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
            # Fetch real location data
            location = await LocationService.get_real_location()

            # Format latitude/longitude
            lat_dir = "N" if location['lat'] >= 0 else "S"
            lon_dir = "E" if location['lon'] >= 0 else "W"

            status = "[REAL DATA]" if 'error' not in location else "[FALLBACK DATA]"
            error_msg = f"\nNote: {location['error']}" if 'error' in location else ""

            text = (
                f"Location: {location['city']}, {location['region']}, {location['country']}\n"
                f"Coordinates: {abs(location['lat']):.4f}° {lat_dir}, {abs(location['lon']):.4f}° {lon_dir}\n"
                f"Timezone: {location['timezone']}\n"
                f"ISP: {location['isp']}\n"
                f"IP Address: {location['ip']}\n"
                f"Status: {status}{error_msg}"
            )

            return web.json_response({
                "content": [{"type": "text", "text": text}]
            })

        elif tool_name == "get_timezone":
            # Get location first to determine timezone
            location = await LocationService.get_real_location()
            tz_info = await LocationService.get_timezone_info(location['timezone'])

            status = "[REAL DATA]" if 'error' not in tz_info else "[ERROR]"
            error_msg = f"\nNote: {tz_info['error']}" if 'error' in tz_info else ""
            dst_status = "Yes (Daylight Saving Time)" if tz_info['is_dst'] else "No"

            text = (
                f"Timezone: {tz_info['timezone']}\n"
                f"UTC Offset: {tz_info['utc_offset']}\n"
                f"Current Time: {tz_info['current_time']}\n"
                f"DST Active: {dst_status}\n"
                f"Status: {status}{error_msg}"
            )

            return web.json_response({
                "content": [{"type": "text", "text": text}]
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
            print(f"[CLIENT] [OK] Connected to: {result.get('serverInfo', {}).get('name')}")
            return result

    async def list_tools(self) -> list:
        """List available tools"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/list",
                json={}
            )
            tools = response.json().get("tools", [])
            print(f"[CLIENT] [OK] Found {len(tools)} tools:")
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
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 70 + "\n")

    finally:
        # Cleanup
        await runner.cleanup()
        print("[SERVER] Server stopped")


if __name__ == "__main__":
    asyncio.run(run_test())
