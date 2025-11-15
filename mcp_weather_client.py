#!/usr/bin/env python3
"""
MCP Client for Weather Services
This script connects to an MCP server to get current weather conditions.
It integrates with the location MCP client to get coordinates first.
"""

import asyncio
import json
from typing import Any, Dict, Optional
import httpx


class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, server_url: str, client_name: str = "weather-client"):
        self.server_url = server_url
        self.client_name = client_name
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
                        "name": self.client_name,
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


async def get_location_data() -> Optional[Dict[str, Any]]:
    """Get location data from location MCP server or fallback to IP-based location"""
    location_server_url = "http://localhost:3000/mcp"

    try:
        # Try MCP location server first
        client = MCPClient(location_server_url, "weather-location-client")
        await client.initialize()
        result = await client.call_tool("get_location")

        # Parse location from response
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                # Extract coordinates from text (simple parsing)
                # Format expected: "Coordinates: lat, lon"
                if "Coordinates:" in text:
                    coords_line = [line for line in text.split('\n') if 'Coordinates:' in line][0]
                    coords_str = coords_line.split('Coordinates:')[1].strip()
                    # Remove degree symbols and directions
                    coords_str = coords_str.replace('°', '').replace('N', '').replace('S', '').replace('E', '').replace('W', '').replace(',', '')
                    parts = coords_str.split()
                    if len(parts) >= 2:
                        return {
                            "latitude": float(parts[0]),
                            "longitude": float(parts[1])
                        }

    except Exception as e:
        print(f"Could not connect to location MCP server: {e}")
        print("Falling back to IP-based location...")

    # Fallback to IP-based location
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://ipapi.co/json/")
            data = response.json()
            return {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "city": data.get("city"),
                "country": data.get("country_name")
            }
    except Exception as e:
        print(f"Error getting location: {e}")
        return None


async def get_weather_via_mcp(latitude: float, longitude: float):
    """
    Get current weather using an MCP weather server.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    """

    # MCP weather server URL
    mcp_server_url = "http://localhost:3001/mcp"

    print("=" * 60)
    print("MCP Weather Client - Current Conditions")
    print("=" * 60)

    try:
        # Create MCP client
        client = MCPClient(mcp_server_url, "weather-client")

        # Initialize connection
        print("\n[1] Initializing MCP connection...")
        await client.initialize()

        # List available tools
        print("\n[2] Discovering available weather tools...")
        tools = await client.list_tools()

        # Call current weather tool
        print(f"\n[3] Requesting current weather for coordinates: {latitude}, {longitude}...")
        result = await client.call_tool(
            "get_current_weather",
            arguments={
                "latitude": latitude,
                "longitude": longitude
            }
        )

        # Display results
        print("\n" + "=" * 60)
        print("CURRENT WEATHER CONDITIONS")
        print("=" * 60)

        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                print(item.get("text"))

        return result

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to MCP weather server")
        print("   Make sure the MCP weather server is running at:", mcp_server_url)
        print("\nAlternative: Using free weather API...")
        await get_weather_via_api(latitude, longitude)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFalling back to direct weather API...")
        await get_weather_via_api(latitude, longitude)


async def get_weather_via_api(latitude: float, longitude: float):
    """
    Fallback method: Get current weather using Open-Meteo API (free, no API key needed)
    This doesn't use MCP but demonstrates weather retrieval
    """
    print("\n" + "=" * 60)
    print("Weather API Lookup (Fallback)")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Using Open-Meteo free API
            url = f"https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto"
            }

            response = await client.get(url, params=params)
            data = response.json()

            current = data.get("current", {})

            # Weather code interpretation
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                77: "Snow grains",
                80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }

            weather_code = current.get("weather_code", 0)
            weather_desc = weather_codes.get(weather_code, "Unknown")

            print(f"\n☀️  Current Weather Conditions:")
            print(f"   Location: {latitude}°, {longitude}°")
            print(f"   Conditions: {weather_desc}")
            print(f"   Temperature: {current.get('temperature_2m', 'N/A')}°F")
            print(f"   Feels Like: {current.get('apparent_temperature', 'N/A')}°F")
            print(f"   Humidity: {current.get('relative_humidity_2m', 'N/A')}%")
            print(f"   Wind Speed: {current.get('wind_speed_10m', 'N/A')} mph")
            print(f"   Wind Direction: {current.get('wind_direction_10m', 'N/A')}°")
            print(f"   Cloud Cover: {current.get('cloud_cover', 'N/A')}%")
            print(f"   Precipitation: {current.get('precipitation', 'N/A')} mm")
            print(f"   Last Updated: {current.get('time', 'N/A')}")

            return data

    except Exception as e:
        print(f"❌ Error getting weather: {e}")


async def main():
    """Main function to get location and weather"""
    print("\n🌤️  MCP Weather Service Client\n")
    print("This script gets current weather conditions using MCP protocol.")
    print("If no MCP server is available, it falls back to weather API.\n")

    # Get location first
    print("[Step 1] Getting current location...")
    location = await get_location_data()

    if not location:
        print("❌ Could not determine location. Exiting.")
        return

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if location.get("city"):
        print(f"✓ Location determined: {location.get('city')}, {location.get('country')}")

    print(f"✓ Coordinates: {latitude}, {longitude}\n")

    # Get weather for location
    print("[Step 2] Getting current weather conditions...")
    await get_weather_via_mcp(latitude, longitude)


if __name__ == "__main__":
    asyncio.run(main())
