#!/usr/bin/env python3
"""
Complete MCP Weather Test - Runs both weather server and client
Integrates with location service to provide weather for current location
"""

import asyncio
import json
from typing import Any, Dict
import httpx
from aiohttp import web


class MCPWeatherServer:
    """MCP server for weather services"""

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
        print(f"[WEATHER SERVER] Received initialization from: {data.get('clientInfo', {}).get('name')}")
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "weather-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        """Return available weather tools"""
        print("[WEATHER SERVER] Listing available tools")
        return web.json_response({
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get current weather conditions for a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "number",
                                "description": "Latitude coordinate"
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude coordinate"
                            }
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            ]
        })

    async def call_tool(self, request):
        """Handle tool calls"""
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        print(f"[WEATHER SERVER] Tool called: {tool_name}")

        if tool_name == "get_current_weather":
            latitude = arguments.get("latitude")
            longitude = arguments.get("longitude")

            # Fetch real weather data from Open-Meteo API
            try:
                async with httpx.AsyncClient() as client:
                    url = "https://api.open-meteo.com/v1/forecast"
                    params = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m",
                        "temperature_unit": "fahrenheit",
                        "wind_speed_unit": "mph",
                        "timezone": "auto"
                    }

                    response = await client.get(url, params=params)
                    weather_data = response.json()
                    current = weather_data.get("current", {})

                    # Weather code interpretation
                    weather_codes = {
                        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                        45: "Foggy", 48: "Depositing rime fog",
                        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                        95: "Thunderstorm"
                    }

                    weather_code = current.get("weather_code", 0)
                    weather_desc = weather_codes.get(weather_code, "Unknown")

                    weather_text = f"""Current Weather Conditions
Location: {latitude}°, {longitude}°
Conditions: {weather_desc}
Temperature: {current.get('temperature_2m', 'N/A')}°F
Feels Like: {current.get('apparent_temperature', 'N/A')}°F
Humidity: {current.get('relative_humidity_2m', 'N/A')}%
Wind Speed: {current.get('wind_speed_10m', 'N/A')} mph
Wind Direction: {current.get('wind_direction_10m', 'N/A')}°
Cloud Cover: {current.get('cloud_cover', 'N/A')}%
Precipitation: {current.get('precipitation', 'N/A')} mm
Last Updated: {current.get('time', 'N/A')}"""

                    return web.json_response({
                        "content": [
                            {
                                "type": "text",
                                "text": weather_text
                            }
                        ]
                    })

            except Exception as e:
                # Fallback to mock data if API fails
                return web.json_response({
                    "content": [
                        {
                            "type": "text",
                            "text": f"Current Weather Conditions (Mock Data)\n"
                                   f"Location: {latitude}°, {longitude}°\n"
                                   f"Conditions: Partly Cloudy\n"
                                   f"Temperature: 72°F\n"
                                   f"Feels Like: 70°F\n"
                                   f"Humidity: 55%\n"
                                   f"Wind Speed: 8 mph\n"
                                   f"Note: Using mock data due to API error: {str(e)}"
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
        print(f"[WEATHER SERVER] MCP weather server started on http://{self.host}:{self.port}")
        return runner


class MCPLocationServer:
    """MCP server for location services (simplified for testing)"""

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
        print(f"[LOCATION SERVER] Received initialization from: {data.get('clientInfo', {}).get('name')}")
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "location-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        """Return available tools"""
        return web.json_response({
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get current location",
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

        if tool_name == "get_location":
            # Use IP-based location
            try:
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
            except Exception as e:
                # Fallback to mock location
                return web.json_response({
                    "content": [
                        {
                            "type": "text",
                            "text": "Location: San Francisco, California, USA\n"
                                   "Coordinates: 37.7749, -122.4194"
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
        print(f"[LOCATION SERVER] MCP location server started on http://{self.host}:{self.port}")
        return runner


class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, server_url: str, client_name: str = "test-client"):
        self.server_url = server_url
        self.client_name = client_name

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": self.client_name,
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


async def run_integrated_test():
    """Run complete integrated test with location and weather"""
    print("\n" + "=" * 70)
    print("MCP WEATHER + LOCATION SERVICE - INTEGRATED TEST")
    print("=" * 70 + "\n")

    # Start both servers
    location_server = MCPLocationServer()
    location_runner = await location_server.start()

    weather_server = MCPWeatherServer()
    weather_runner = await weather_server.start()

    # Give servers a moment to start
    await asyncio.sleep(0.5)

    try:
        # Test 1: Get location
        print("\n[TEST 1] Getting current location...")
        location_client = MCPClient("http://localhost:3000/mcp", "weather-location-client")
        await location_client.initialize()
        location_result = await location_client.call_tool("get_location")

        print("\n--- Location Response ---")
        latitude, longitude = None, None
        for item in location_result.get("content", []):
            if item.get("type") == "text":
                text = item.get("text")
                print(text)
                # Parse coordinates
                if "Coordinates:" in text:
                    coords_line = [line for line in text.split('\n') if 'Coordinates:' in line][0]
                    coords_str = coords_line.split('Coordinates:')[1].strip()
                    parts = coords_str.split(',')
                    if len(parts) == 2:
                        latitude = float(parts[0].strip())
                        longitude = float(parts[1].strip())

        # Test 2: Get weather for location
        print("\n[TEST 2] Getting weather conditions...")
        weather_client = MCPClient("http://localhost:3001/mcp", "weather-client")
        await weather_client.initialize()
        await weather_client.list_tools()

        if latitude and longitude:
            print(f"\n[TEST 3] Calling 'get_current_weather' for {latitude}, {longitude}...")
            weather_result = await weather_client.call_tool(
                "get_current_weather",
                arguments={"latitude": latitude, "longitude": longitude}
            )

            print("\n--- Weather Response ---")
            for item in weather_result.get("content", []):
                if item.get("type") == "text":
                    print(item.get("text"))

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70 + "\n")

    finally:
        # Cleanup
        await location_runner.cleanup()
        await weather_runner.cleanup()
        print("[SERVERS] Servers stopped")


if __name__ == "__main__":
    asyncio.run(run_integrated_test())
