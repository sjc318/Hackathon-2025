#!/usr/bin/env python3
"""
Run MCP Location and Weather Servers
Keeps both servers running until interrupted with Ctrl+C
"""

import asyncio
import httpx
from aiohttp import web


class MCPLocationServer:
    """MCP server for location services"""

    def __init__(self, host='localhost', port=3000):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_post('/mcp/initialize', self.initialize)
        self.app.router.add_post('/mcp/tools/list', self.list_tools)
        self.app.router.add_post('/mcp/tools/call', self.call_tool)

    async def initialize(self, request):
        data = await request.json()
        print(f"[LOCATION] Client connected: {data.get('clientInfo', {}).get('name')}")
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "location-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        return web.json_response({
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get current location",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        })

    async def call_tool(self, request):
        data = await request.json()
        if data.get("name") == "get_location":
            # Mock location data (APIs blocked in this environment)
            return web.json_response({
                "content": [{
                    "type": "text",
                    "text": "Location: San Francisco, California, USA\n"
                           "Coordinates: 37.7749, -122.4194"
                }]
            })
        return web.json_response({"error": "Unknown tool"}, status=400)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"✓ Location MCP Server: http://{self.host}:{self.port}")
        return runner


class MCPWeatherServer:
    """MCP server for weather services"""

    def __init__(self, host='localhost', port=3001):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        self.app.router.add_post('/mcp/initialize', self.initialize)
        self.app.router.add_post('/mcp/tools/list', self.list_tools)
        self.app.router.add_post('/mcp/tools/call', self.call_tool)

    async def initialize(self, request):
        data = await request.json()
        print(f"[WEATHER] Client connected: {data.get('clientInfo', {}).get('name')}")
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "weather-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(self, request):
        return web.json_response({
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get current weather conditions for a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number", "description": "Latitude coordinate"},
                            "longitude": {"type": "number", "description": "Longitude coordinate"}
                        },
                        "required": ["latitude", "longitude"]
                    }
                }
            ]
        })

    async def call_tool(self, request):
        data = await request.json()
        arguments = data.get("arguments", {})

        if data.get("name") == "get_current_weather":
            lat = arguments.get("latitude", 37.7749)
            lon = arguments.get("longitude", -122.4194)

            # Mock weather data (APIs blocked in this environment)
            return web.json_response({
                "content": [{
                    "type": "text",
                    "text": f"""Current Weather Conditions
Location: {lat}°, {lon}°
Conditions: Partly Cloudy
Temperature: 58°F
Feels Like: 56°F
Humidity: 65%
Wind Speed: 10 mph
Wind Direction: 270°
Cloud Cover: 40%
Precipitation: 0 mm
Note: Mock data (external APIs blocked in this environment)"""
                }]
            })

        return web.json_response({"error": "Unknown tool"}, status=400)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"✓ Weather MCP Server: http://{self.host}:{self.port}")
        return runner


async def main():
    print("\n" + "=" * 60)
    print("Starting MCP Servers")
    print("=" * 60 + "\n")

    # Start both servers
    location_server = MCPLocationServer()
    location_runner = await location_server.start()

    weather_server = MCPWeatherServer()
    weather_runner = await weather_server.start()

    print("\n" + "=" * 60)
    print("Servers Running - Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    try:
        # Keep running forever
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        await location_runner.cleanup()
        await weather_runner.cleanup()
        print("Servers stopped.\n")


if __name__ == "__main__":
    asyncio.run(main())
