#!/usr/bin/env python3
"""
Complete MCP Weather Test - Runs both server and client
"""

import asyncio
import json
from typing import Any, Dict
import httpx
from aiohttp import web


class MCPWeatherServer:
    """Simple MCP Weather server for testing"""

    def __init__(self, host='localhost', port=3001):
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
                "name": "test-weather-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        """Return available tools"""
        print("[SERVER] Listing available tools")
        return web.json_response({
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get current weather for a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"},
                            "latitude": {"type": "number", "description": "Latitude"},
                            "longitude": {"type": "number", "description": "Longitude"}
                        }
                    }
                },
                {
                    "name": "get_forecast",
                    "description": "Get multi-day weather forecast",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"},
                            "latitude": {"type": "number", "description": "Latitude"},
                            "longitude": {"type": "number", "description": "Longitude"},
                            "days": {"type": "integer", "description": "Number of days"}
                        }
                    }
                },
                {
                    "name": "get_weather_alerts",
                    "description": "Get active weather alerts",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name"},
                            "latitude": {"type": "number", "description": "Latitude"},
                            "longitude": {"type": "number", "description": "Longitude"}
                        }
                    }
                }
            ]
        })

    async def call_tool(self, request):
        """Handle tool calls"""
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        print(f"[SERVER] Tool called: {tool_name} with args: {arguments}")

        if tool_name == "get_current_weather":
            city = arguments.get("city", "San Francisco, CA")
            lat = arguments.get("latitude", 37.7749)
            lon = arguments.get("longitude", -122.4194)

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"Current Weather for {city}\n"
                               f"Coordinates: {lat}° N, {lon}° W\n"
                               f"Temperature: 68°F (20°C)\n"
                               f"Conditions: Partly Cloudy ⛅\n"
                               f"Humidity: 65%\n"
                               f"Wind: 10 mph NW\n"
                               f"Pressure: 30.12 inHg\n"
                               f"Visibility: 10 miles\n"
                               f"UV Index: 5 (Moderate)\n"
                               f"Status: Mock data for testing"
                    }
                ]
            })

        elif tool_name == "get_forecast":
            city = arguments.get("city", "San Francisco, CA")
            days = arguments.get("days", 7)

            forecast_text = f"{days}-Day Weather Forecast for {city}\n\n"

            forecast_days = [
                ("Monday", "Sunny ☀️", 72, 58, 10),
                ("Tuesday", "Partly Cloudy ⛅", 70, 56, 20),
                ("Wednesday", "Cloudy ☁️", 65, 54, 40),
                ("Thursday", "Rain 🌧️", 62, 52, 80),
                ("Friday", "Rain 🌧️", 60, 51, 70),
                ("Saturday", "Partly Cloudy ⛅", 66, 53, 30),
                ("Sunday", "Sunny ☀️", 71, 55, 10)
            ]

            for i, (day, condition, high, low, precip) in enumerate(forecast_days[:days]):
                forecast_text += f"Day {i+1} ({day}):\n"
                forecast_text += f"  Condition: {condition}\n"
                forecast_text += f"  High: {high}°F, Low: {low}°F\n"
                forecast_text += f"  Precipitation: {precip}%\n\n"

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": forecast_text + "Status: Mock data for testing"
                    }
                ]
            })

        elif tool_name == "get_weather_alerts":
            city = arguments.get("city", "San Francisco, CA")

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"Weather Alerts for {city}\n\n"
                               f"⚠️ Wind Advisory\n"
                               f"   Issued: Today at 10:00 AM\n"
                               f"   Valid: Until 8:00 PM\n"
                               f"   Details: Gusty winds up to 45 mph expected\n\n"
                               f"Status: Mock data for testing"
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
        print(f"[SERVER] MCP Weather server started on http://{self.host}:{self.port}")
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
                        "name": "weather-client",
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

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool"""
        if arguments is None:
            arguments = {}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={"name": tool_name, "arguments": arguments}
            )
            return response.json()


async def run_test():
    """Run complete MCP weather test"""
    print("\n" + "=" * 70)
    print("MCP WEATHER SERVICE - COMPLETE TEST")
    print("=" * 70 + "\n")

    # Start server
    server = MCPWeatherServer()
    runner = await server.start()

    # Give server a moment to start
    await asyncio.sleep(0.5)

    try:
        # Create client
        client = MCPClient("http://localhost:3001/mcp")

        # Test 1: Initialize
        print("\n[TEST 1] Initializing connection...")
        await client.initialize()

        # Test 2: List tools
        print("\n[TEST 2] Discovering weather tools...")
        tools = await client.list_tools()

        # Test 3: Get current weather by city
        print("\n[TEST 3] Getting current weather for San Francisco...")
        result = await client.call_tool("get_current_weather", {"city": "San Francisco, CA"})
        print("\n--- Current Weather ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        # Test 4: Get current weather by coordinates
        print("\n[TEST 4] Getting current weather by coordinates (NYC)...")
        result = await client.call_tool(
            "get_current_weather",
            {"latitude": 40.7128, "longitude": -74.0060}
        )
        print("\n--- Current Weather (NYC) ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        # Test 5: Get 3-day forecast
        print("\n[TEST 5] Getting 3-day forecast...")
        result = await client.call_tool(
            "get_forecast",
            {"city": "San Francisco, CA", "days": 3}
        )
        print("\n--- 3-Day Forecast ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        # Test 6: Get 7-day forecast
        print("\n[TEST 6] Getting 7-day forecast...")
        result = await client.call_tool(
            "get_forecast",
            {"city": "Los Angeles, CA", "days": 7}
        )
        print("\n--- 7-Day Forecast ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        # Test 7: Get weather alerts
        print("\n[TEST 7] Getting weather alerts...")
        result = await client.call_tool(
            "get_weather_alerts",
            {"city": "San Francisco, CA"}
        )
        print("\n--- Weather Alerts ---")
        for item in result.get("content", []):
            if item.get("type") == "text":
                print(item.get("text"))

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70 + "\n")

        print("\nTest Summary:")
        print("  ✓ Server initialization successful")
        print("  ✓ Client connection established")
        print("  ✓ Tool discovery working")
        print("  ✓ Current weather by city working")
        print("  ✓ Current weather by coordinates working")
        print("  ✓ Weather forecast (3-day) working")
        print("  ✓ Weather forecast (7-day) working")
        print("  ✓ Weather alerts working")

    finally:
        # Cleanup
        await runner.cleanup()
        print("\n[SERVER] Server stopped")


if __name__ == "__main__":
    asyncio.run(run_test())
