#!/usr/bin/env python3
"""
MCP Weather Server for Claude Desktop
This is a stdio-based MCP server that provides weather services via JSON-RPC.
"""

import asyncio
import json
import sys
from typing import Any, Dict, Optional
import httpx


class StdioMCPWeatherServer:
    """MCP Server that provides weather information via stdio (for Claude Desktop)"""

    def __init__(self):
        self.running = True

    async def get_real_location(self) -> Dict[str, Any]:
        """Get real location data from IP geolocation API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                    }
                else:
                    raise Exception("API returned error status")
        except Exception as e:
            # Fallback to default location
            return {
                'city': 'San Francisco',
                'region': 'California',
                'country': 'USA',
                'lat': 37.7749,
                'lon': -122.4194,
                'timezone': 'America/Los_Angeles',
                'error': str(e)
            }

    async def get_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get weather data from Open-Meteo API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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
                response.raise_for_status()
                weather_data = response.json()
                current = weather_data.get("current", {})

                # Weather code interpretation
                weather_codes = {
                    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
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

                return {
                    'conditions': weather_desc,
                    'temperature': current.get('temperature_2m'),
                    'feels_like': current.get('apparent_temperature'),
                    'humidity': current.get('relative_humidity_2m'),
                    'wind_speed': current.get('wind_speed_10m'),
                    'wind_direction': current.get('wind_direction_10m'),
                    'cloud_cover': current.get('cloud_cover'),
                    'precipitation': current.get('precipitation'),
                    'time': current.get('time')
                }
        except Exception as e:
            return {
                'error': str(e),
                'conditions': 'Unknown',
                'temperature': None,
                'feels_like': None,
                'humidity': None,
                'wind_speed': None
            }

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "weather-mcp-server",
                "version": "1.0.0"
            }
        }

    def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "Get current weather conditions for a location (uses IP-based location if no coordinates provided)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "latitude": {
                                "type": "number",
                                "description": "Latitude coordinate (optional, will use IP location if not provided)"
                            },
                            "longitude": {
                                "type": "number",
                                "description": "Longitude coordinate (optional, will use IP location if not provided)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "get_weather_for_location",
                    "description": "Get current weather for your IP-based location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ]
        }

    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "get_current_weather":
            # Get coordinates from arguments or use IP-based location
            latitude = arguments.get("latitude")
            longitude = arguments.get("longitude")

            if latitude is None or longitude is None:
                # Get location from IP
                location = await self.get_real_location()
                latitude = location['lat']
                longitude = location['lon']
                location_text = f"{location['city']}, {location['region']}, {location['country']}"
                location_note = f" (IP-based location: {location_text})"
            else:
                location_note = ""

            # Get weather
            weather = await self.get_weather(latitude, longitude)

            status = "[REAL DATA]" if 'error' not in weather else f"[ERROR: {weather['error']}]"

            text = (
                f"Current Weather Conditions{location_note}\n"
                f"Location: {latitude:.4f}, {longitude:.4f}\n"
                f"Conditions: {weather['conditions']}\n"
                f"Temperature: {weather['temperature']}°F\n"
                f"Feels Like: {weather['feels_like']}°F\n"
                f"Humidity: {weather['humidity']}%\n"
                f"Wind Speed: {weather['wind_speed']} mph\n"
                f"Wind Direction: {weather['wind_direction']}°\n"
                f"Cloud Cover: {weather['cloud_cover']}%\n"
                f"Precipitation: {weather['precipitation']} mm\n"
                f"Last Updated: {weather['time']}\n"
                f"Status: {status}"
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }

        elif tool_name == "get_weather_for_location":
            # Get location from IP
            location = await self.get_real_location()
            latitude = location['lat']
            longitude = location['lon']

            # Get weather
            weather = await self.get_weather(latitude, longitude)

            status = "[REAL DATA]" if 'error' not in weather and 'error' not in location else "[PARTIAL DATA]"
            if 'error' in location:
                status = f"[LOCATION FALLBACK: {location['error']}]"

            text = (
                f"Current Weather for Your Location\n"
                f"Location: {location['city']}, {location['region']}, {location['country']}\n"
                f"Coordinates: {latitude:.4f}°, {longitude:.4f}°\n"
                f"Conditions: {weather['conditions']}\n"
                f"Temperature: {weather['temperature']}°F\n"
                f"Feels Like: {weather['feels_like']}°F\n"
                f"Humidity: {weather['humidity']}%\n"
                f"Wind Speed: {weather['wind_speed']} mph\n"
                f"Wind Direction: {weather['wind_direction']}°\n"
                f"Cloud Cover: {weather['cloud_cover']}%\n"
                f"Precipitation: {weather['precipitation']} mm\n"
                f"Timezone: {location['timezone']}\n"
                f"Last Updated: {weather['time']}\n"
                f"Status: {status}"
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        else:
            raise Exception(f"Unknown tool: {tool_name}")

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate handler"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            result = self.handle_initialize(params)
        elif method == "tools/list":
            result = self.handle_list_tools(params)
        elif method == "tools/call":
            result = await self.handle_call_tool(params)
        else:
            raise Exception(f"Unknown method: {method}")

        return result

    def send_response(self, response_id: Optional[Any], result: Any = None, error: Any = None):
        """Send JSON-RPC response to stdout"""
        response = {
            "jsonrpc": "2.0",
            "id": response_id
        }

        if error:
            response["error"] = {
                "code": -32603,
                "message": str(error)
            }
        else:
            response["result"] = result

        # Write to stdout
        output = json.dumps(response) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()

    async def run(self):
        """Main server loop - reads from stdin and processes requests"""
        # Send initial message to stderr for debugging
        print("MCP Weather Server started", file=sys.stderr)

        loop = asyncio.get_event_loop()

        while self.running:
            try:
                # Read from stdin
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    # EOF reached
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse JSON-RPC request
                request = json.loads(line)
                request_id = request.get("id")

                try:
                    # Handle request
                    result = await self.handle_request(request)
                    self.send_response(request_id, result=result)

                except Exception as e:
                    print(f"Error handling request: {e}", file=sys.stderr)
                    self.send_response(request_id, error=str(e))

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)


async def main():
    """Main entry point"""
    server = StdioMCPWeatherServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
