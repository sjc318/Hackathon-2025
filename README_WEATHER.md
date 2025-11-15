# MCP Weather Client

A Model Context Protocol (MCP) client implementation for accessing weather services.

## Overview

This project provides an MCP client for weather services that can:
- Connect to MCP weather servers
- Get current weather conditions
- Retrieve multi-day forecasts
- Check weather alerts
- Fallback to public weather APIs when MCP server is unavailable

## Files

- `mcp_weather_client.py` - Main weather client implementation
- `test_mcp_weather.py` - Comprehensive integration tests with mock MCP server
- `requirements.txt` - Python package dependencies

## Features

### MCP Weather Tools

1. **get_current_weather** - Get current weather conditions
   - By city name: `{"city": "San Francisco, CA"}`
   - By coordinates: `{"latitude": 37.7749, "longitude": -122.4194}`

2. **get_forecast** - Get multi-day weather forecast
   - Supports 1-7 day forecasts
   - Parameters: city/coordinates + days

3. **get_weather_alerts** - Get active weather alerts
   - Severe weather warnings
   - Advisory notifications

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Running the Weather Client

```bash
# Get weather for a city
python3 mcp_weather_client.py "San Francisco, CA"

# Get weather for another city
python3 mcp_weather_client.py "New York, NY"

# Get weather by coordinates
python3 mcp_weather_client.py "37.7749,-122.4194"
```

### Running Integration Tests

```bash
python3 test_mcp_weather.py
```

The test suite will:
1. Start a mock MCP weather server
2. Connect the client to the server
3. Test all weather tools
4. Verify responses
5. Clean up and shut down

## MCP Protocol Implementation

The client implements the MCP protocol version 2024-11-05:

### Initialization
```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {"tools": {}},
  "clientInfo": {
    "name": "weather-client",
    "version": "1.0.0"
  }
}
```

### Tool Discovery
The client can discover available tools from the MCP server via the `/tools/list` endpoint.

### Tool Invocation
Tools are called via the `/tools/call` endpoint with the tool name and arguments.

## Fallback Mechanism

When an MCP server is not available, the client automatically falls back to:
- Open-Meteo public weather API (free, no API key required)
- Geocoding for city name lookups
- Real-time weather data retrieval

## Example Output

```
============================================================
MCP Weather Client
============================================================

[1] Initializing MCP connection...
✓ Connected to MCP server: test-weather-mcp-server

[2] Discovering available weather tools...
✓ Available tools: 3
  - get_current_weather: Get current weather for a location
  - get_forecast: Get multi-day weather forecast
  - get_weather_alerts: Get active weather alerts

[3] Requesting current weather...

============================================================
CURRENT WEATHER
============================================================
Current Weather for San Francisco, CA
Coordinates: 37.7749° N, -122.4194° W
Temperature: 68°F (20°C)
Conditions: Partly Cloudy ⛅
Humidity: 65%
Wind: 10 mph NW
Pressure: 30.12 inHg
Visibility: 10 miles
UV Index: 5 (Moderate)
```

## Architecture

### MCPClient Class

The base client class handles:
- Server initialization
- Tool discovery
- Tool invocation
- Session management

### Weather-Specific Functions

- `get_weather_via_mcp()` - Main MCP weather retrieval
- `get_weather_via_api()` - Fallback API implementation

## Integration with Other MCP Clients

This weather client follows the same pattern as `mcp_location_client.py`:
- Shared `MCPClient` base class
- Similar server communication patterns
- Consistent error handling
- Fallback mechanisms

## Testing

The test suite (`test_mcp_weather.py`) provides:
- Mock MCP server implementation
- Comprehensive tool testing
- Client-server integration validation
- Automated test execution

All tests validate:
- ✓ Server initialization
- ✓ Client connection
- ✓ Tool discovery
- ✓ Weather by city
- ✓ Weather by coordinates
- ✓ 3-day and 7-day forecasts
- ✓ Weather alerts

## Future Enhancements

Potential improvements:
- Historical weather data support
- Hourly forecasts
- Weather radar integration
- Air quality index
- UV index predictions
- Precipitation radar
- Marine weather conditions
- Astronomical data (sunrise/sunset)

## License

This is a demonstration project for MCP protocol implementation.

## Related Projects

- `mcp_location_client.py` - MCP client for location services
- `test_mcp_complete.py` - Location client integration tests
