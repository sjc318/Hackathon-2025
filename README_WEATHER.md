# MCP Weather Service Client

This directory contains an MCP (Model Context Protocol) client for weather services that provides current weather conditions based on location data from the MCP location service.

## Files

- **mcp_weather_client.py** - Main weather client that integrates with location service
- **test_mcp_weather.py** - Complete integration test with both location and weather servers

## Features

- **MCP Protocol Integration**: Implements the MCP 2024-11-05 protocol specification
- **Location Integration**: Automatically gets location from the location MCP service
- **Current Weather Only**: Focused on current weather conditions (not forecasts)
- **Fallback Support**: Falls back to direct weather API if MCP server is unavailable
- **Real Weather Data**: Uses Open-Meteo API for actual weather conditions

## Weather Data Provided

The weather client provides the following current conditions:

- Weather description (clear, cloudy, rain, snow, etc.)
- Temperature (°F)
- Feels like temperature
- Humidity (%)
- Wind speed (mph)
- Wind direction (degrees)
- Cloud cover (%)
- Precipitation (mm)
- Last update timestamp

## Installation

Install required dependencies:

```bash
pip install httpx aiohttp
```

## Usage

### Running the Integrated Test

This test runs both location and weather MCP servers and demonstrates the complete integration:

```bash
python3 test_mcp_weather.py
```

### Using the Weather Client

```bash
python3 mcp_weather_client.py
```

The client will:
1. Get your current location (from MCP location service or IP-based lookup)
2. Fetch current weather for your location (from MCP weather service or direct API)
3. Display the current weather conditions

## Architecture

### MCP Weather Server

The weather MCP server provides one tool:

- **get_current_weather**: Gets current weather conditions
  - Required parameters: `latitude` (number), `longitude` (number)
  - Returns: Current weather conditions as text

### Integration Flow

```
User Request
    ↓
[1] Location Client → Location MCP Server → Get Coordinates
    ↓
[2] Weather Client → Weather MCP Server → Get Weather for Coordinates
    ↓
Display Results
```

### Fallback Behavior

If MCP servers are unavailable:
- Location falls back to IP-based geolocation (ipapi.co)
- Weather falls back to direct Open-Meteo API calls

## Example Output

```
======================================================================
MCP WEATHER + LOCATION SERVICE - INTEGRATED TEST
======================================================================

[TEST 1] Getting current location...
[CLIENT] ✓ Connected to: location-mcp-server

--- Location Response ---
Location: San Francisco, California, USA
Coordinates: 37.7749, -122.4194

[TEST 2] Getting weather conditions...
[CLIENT] ✓ Connected to: weather-mcp-server
[CLIENT] ✓ Found 1 tools:
         - get_current_weather: Get current weather conditions for a location

[TEST 3] Calling 'get_current_weather' for 37.7749, -122.4194...

--- Weather Response ---
Current Weather Conditions
Location: 37.7749°, -122.4194°
Conditions: Partly Cloudy
Temperature: 58°F
Feels Like: 56°F
Humidity: 72%
Wind Speed: 12 mph
Wind Direction: 290°
Cloud Cover: 45%
Precipitation: 0 mm
Last Updated: 2025-11-15T20:00

======================================================================
✓ ALL TESTS PASSED
======================================================================
```

## API Information

### Open-Meteo API

- **URL**: https://api.open-meteo.com/v1/forecast
- **License**: Free, no API key required
- **Rate Limits**: 10,000 requests/day
- **Documentation**: https://open-meteo.com/en/docs

### IP Geolocation API (fallback)

- **URL**: https://ipapi.co/json/
- **License**: Free tier available
- **Rate Limits**: 1,000 requests/day (free tier)

## MCP Protocol Details

The client implements MCP protocol version 2024-11-05:

- **Initialization**: Establishes connection with server capabilities
- **Tool Discovery**: Lists available tools from the server
- **Tool Execution**: Calls tools with proper argument schemas

## Notes

- The weather client focuses on current conditions only (no forecasts)
- Temperature is returned in Fahrenheit
- Wind speed is in mph
- Coordinates are required in decimal degrees format
- Weather codes are mapped to human-readable descriptions

## Integration with Location Service

The weather client seamlessly integrates with the location MCP service:

1. Calls the location service to get current coordinates
2. Parses the location response to extract latitude/longitude
3. Uses coordinates to fetch weather from the weather service
4. Displays both location and weather information

## Error Handling

The client includes robust error handling:

- Connection errors trigger fallback to direct APIs
- API failures use mock data for testing
- Invalid coordinates are handled gracefully
- Network timeouts are caught and reported
