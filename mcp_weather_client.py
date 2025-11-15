#!/usr/bin/env python3
"""
MCP Client for Weather Services
This script connects to a public MCP server to get weather information.
"""

import asyncio
import json
from typing import Any, Dict, Optional
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
                        "name": "weather-client",
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


async def get_weather_via_mcp(city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None):
    """
    Get weather information using an MCP server.

    Args:
        city: City name (e.g., "San Francisco, CA")
        lat: Latitude coordinate
        lon: Longitude coordinate

    Note: This is a demonstration using a hypothetical weather MCP server.
    In practice, you would use a real MCP server URL that provides weather services.
    """

    # Example MCP server URL (replace with actual public MCP server)
    mcp_server_url = "http://localhost:3000/mcp"

    print("=" * 60)
    print("MCP Weather Client")
    print("=" * 60)

    try:
        # Create MCP client
        client = MCPClient(mcp_server_url)

        # Initialize connection
        print("\n[1] Initializing MCP connection...")
        await client.initialize()

        # List available tools
        print("\n[2] Discovering available weather tools...")
        tools = await client.list_tools()

        # Prepare arguments based on what was provided
        args = {}
        if city:
            args["city"] = city
        elif lat is not None and lon is not None:
            args["latitude"] = lat
            args["longitude"] = lon

        # Call current weather tool
        print("\n[3] Requesting current weather...")
        result = await client.call_tool("get_current_weather", args)

        # Display results
        print("\n" + "=" * 60)
        print("CURRENT WEATHER")
        print("=" * 60)

        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                print(item.get("text"))

        # Get forecast if available
        print("\n[4] Requesting weather forecast...")
        forecast_result = await client.call_tool("get_forecast", args)

        print("\n" + "=" * 60)
        print("WEATHER FORECAST")
        print("=" * 60)

        forecast_content = forecast_result.get("content", [])
        for item in forecast_content:
            if item.get("type") == "text":
                print(item.get("text"))

        return result

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to MCP server")
        print("   Make sure the MCP server is running at:", mcp_server_url)
        print("\nAlternative: Using public weather API...")
        await get_weather_via_api(city, lat, lon)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFalling back to public weather API...")
        await get_weather_via_api(city, lat, lon)


async def get_weather_via_api(city: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None):
    """
    Fallback method: Get weather using a public weather API
    This doesn't use MCP but demonstrates weather retrieval
    """
    print("\n" + "=" * 60)
    print("Public Weather API Lookup (Fallback)")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Using Open-Meteo free weather API (no API key required)
            if city:
                # First geocode the city
                geocode_response = await client.get(
                    f"https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1, "language": "en", "format": "json"}
                )
                geocode_data = geocode_response.json()

                if not geocode_data.get("results"):
                    print(f"❌ Could not find city: {city}")
                    return

                location = geocode_data["results"][0]
                lat = location["latitude"]
                lon = location["longitude"]
                city_name = f"{location['name']}, {location.get('country', 'Unknown')}"
            else:
                city_name = f"Coordinates: {lat}, {lon}"

            # Get current weather and forecast
            weather_response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                    "temperature_unit": "fahrenheit",
                    "wind_speed_unit": "mph",
                    "precipitation_unit": "inch",
                    "timezone": "auto",
                    "forecast_days": 7
                }
            )
            weather_data = weather_response.json()

            # Display current weather
            print(f"\n🌤️  Current Weather for {city_name}")
            print("=" * 60)
            current = weather_data.get("current", {})
            print(f"   Temperature: {current.get('temperature_2m', 'N/A')}°F")
            print(f"   Feels Like: {current.get('apparent_temperature', 'N/A')}°F")
            print(f"   Humidity: {current.get('relative_humidity_2m', 'N/A')}%")
            print(f"   Precipitation: {current.get('precipitation', 'N/A')} in")
            print(f"   Wind Speed: {current.get('wind_speed_10m', 'N/A')} mph")
            print(f"   Wind Direction: {current.get('wind_direction_10m', 'N/A')}°")
            print(f"   Weather Code: {current.get('weather_code', 'N/A')}")

            # Display forecast
            print(f"\n📅 7-Day Forecast")
            print("=" * 60)
            daily = weather_data.get("daily", {})
            times = daily.get("time", [])
            temp_max = daily.get("temperature_2m_max", [])
            temp_min = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            precip_prob = daily.get("precipitation_probability_max", [])

            for i in range(min(7, len(times))):
                print(f"\n   {times[i]}:")
                print(f"      High/Low: {temp_max[i]}°F / {temp_min[i]}°F")
                print(f"      Precipitation: {precip[i]} in ({precip_prob[i]}% chance)")

            return weather_data

    except Exception as e:
        print(f"❌ Error getting weather: {e}")


# Alternative: Simple MCP server example for testing
async def run_simple_weather_mcp_server():
    """
    Example of a simple MCP server that could provide weather services.
    This would run separately from the client.
    """
    from aiohttp import web

    async def initialize(request):
        data = await request.json()
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "weather-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(request):
        return web.json_response({
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get current weather for a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "latitude": {
                                "type": "number",
                                "description": "Latitude coordinate"
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude coordinate"
                            }
                        }
                    }
                },
                {
                    "name": "get_forecast",
                    "description": "Get multi-day weather forecast",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "latitude": {
                                "type": "number",
                                "description": "Latitude coordinate"
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude coordinate"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of forecast days (default: 7)"
                            }
                        }
                    }
                },
                {
                    "name": "get_weather_alerts",
                    "description": "Get active weather alerts for a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name"
                            },
                            "latitude": {
                                "type": "number",
                                "description": "Latitude coordinate"
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude coordinate"
                            }
                        }
                    }
                }
            ]
        })

    async def call_tool(request):
        data = await request.json()
        tool_name = data.get("name")
        arguments = data.get("arguments", {})

        if tool_name == "get_current_weather":
            city = arguments.get("city", "Unknown Location")
            lat = arguments.get("latitude", 37.7749)
            lon = arguments.get("longitude", -122.4194)

            # In a real implementation, this would fetch actual weather data
            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"Current Weather for {city}\n"
                               f"Coordinates: {lat}, {lon}\n"
                               f"Temperature: 68°F\n"
                               f"Conditions: Partly Cloudy\n"
                               f"Humidity: 65%\n"
                               f"Wind: 10 mph NW\n"
                               f"Status: Mock data for testing"
                    }
                ]
            })

        elif tool_name == "get_forecast":
            city = arguments.get("city", "Unknown Location")
            days = arguments.get("days", 7)

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"{days}-Day Forecast for {city}\n\n"
                               f"Day 1: Sunny, High: 72°F, Low: 58°F\n"
                               f"Day 2: Partly Cloudy, High: 70°F, Low: 56°F\n"
                               f"Day 3: Cloudy, High: 65°F, Low: 54°F\n"
                               f"Day 4: Rain, High: 62°F, Low: 52°F\n"
                               f"Day 5: Rain, High: 60°F, Low: 51°F\n"
                               f"Day 6: Partly Cloudy, High: 66°F, Low: 53°F\n"
                               f"Day 7: Sunny, High: 71°F, Low: 55°F\n"
                               f"Status: Mock data for testing"
                    }
                ]
            })

        elif tool_name == "get_weather_alerts":
            city = arguments.get("city", "Unknown Location")

            return web.json_response({
                "content": [
                    {
                        "type": "text",
                        "text": f"Weather Alerts for {city}\n\n"
                               f"No active weather alerts at this time.\n"
                               f"Status: Mock data for testing"
                    }
                ]
            })

        return web.json_response({"error": "Unknown tool"}, status=400)

    app = web.Application()
    app.router.add_post('/mcp/initialize', initialize)
    app.router.add_post('/mcp/tools/list', list_tools)
    app.router.add_post('/mcp/tools/call', call_tool)

    print("Starting Weather MCP server on http://localhost:3000")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()


if __name__ == "__main__":
    import sys

    print("\n🌤️  MCP Weather Service Client\n")
    print("This script demonstrates accessing weather via MCP protocol.")
    print("If no MCP server is available, it falls back to public weather API.\n")

    # Parse command line arguments
    city = None
    lat = None
    lon = None

    if len(sys.argv) > 1:
        if sys.argv[1].replace('.', '').replace('-', '').replace(',', '').replace(' ', '').isdigit():
            # Coordinates provided
            coords = sys.argv[1].split(',')
            if len(coords) == 2:
                lat = float(coords[0].strip())
                lon = float(coords[1].strip())
        else:
            # City name provided
            city = ' '.join(sys.argv[1:])

    # Run the client
    if city or (lat and lon):
        asyncio.run(get_weather_via_mcp(city=city, lat=lat, lon=lon))
    else:
        # Default to San Francisco
        asyncio.run(get_weather_via_mcp(city="San Francisco, CA"))
