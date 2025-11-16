# MCP Weather Server - Claude Desktop Setup

## Overview

The MCP Weather Server provides real-time weather information using:
- **IP-based geolocation** (automatic location detection)
- **Open-Meteo API** (free weather data, no API key needed)

## Features

✅ Two tools available:
1. `get_weather_for_location` - Automatically gets weather for your IP location
2. `get_current_weather` - Gets weather for specific coordinates (optional parameters)

✅ Real weather data including:
- Temperature (°F) and feels-like temperature
- Weather conditions (clear, cloudy, rain, snow, etc.)
- Humidity, wind speed, and direction
- Cloud cover and precipitation
- Timezone and last update time

## Installation

### Step 1: Verify Dependencies

```bash
pip install httpx
```

### Step 2: Test the Server

Run the test to make sure it works:

```bash
python test_weather_server.py
```

You should see real weather data for your location!

### Step 3: Configure Claude Desktop

Open your Claude Desktop config file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the weather server configuration:

```json
{
  "mcpServers": {
    "location": {
      "command": "C:\\Users\\nanda\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": [
        "c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_location_server.py"
      ]
    },
    "weather": {
      "command": "C:\\Users\\nanda\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": [
        "c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_weather_server.py"
      ]
    }
  }
}
```

**Note**:
- Use double backslashes (`\\`) in Windows paths
- Update paths to match your actual file locations
- You can have both location and weather servers!

### Step 4: Restart Claude Desktop

1. Completely quit Claude Desktop (not just close window)
2. Restart it
3. The weather tools should now be available

## Usage in Claude Desktop

### Example 1: Get weather for your location
```
"What's the weather like?"
"Get the current weather"
"Use the get_weather_for_location tool"
```

### Example 2: Get weather for specific coordinates
```
"What's the weather in New York?" (Claude will look up coordinates)
"Get weather for latitude 40.7128, longitude -74.0060"
```

## Test Results

The server has been tested and returns real data:

```
Current Weather for Your Location
Location: Cambridge, England, United Kingdom
Coordinates: 52.1929°, 0.1256°
Conditions: Slight rain
Temperature: 48.7°F
Feels Like: 44.3°F
Humidity: 91%
Wind Speed: 8.2 mph
Wind Direction: 26°
Cloud Cover: 100%
Precipitation: 0.0 mm
Timezone: Europe/London
Status: [REAL DATA]
```

## How It Works

1. **Automatic Location**: Uses ip-api.com to detect your location from IP address
2. **Weather Data**: Fetches current conditions from Open-Meteo API
3. **stdio Protocol**: Communicates with Claude Desktop via JSON-RPC over stdin/stdout
4. **No API Keys**: Both services are free and don't require API keys

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check Python path: `python --version`
2. Test server manually: `python test_weather_server.py`
3. Check Claude Desktop logs: `%APPDATA%\Claude\logs`
4. Verify httpx is installed: `pip install httpx`

### Getting fallback data instead of real data

- Check your internet connection
- The API might be temporarily unavailable
- The server will still work but may use cached/fallback location

## Files Created

- `mcp_weather_server.py` - The main MCP weather server
- `test_weather_server.py` - Test script to verify functionality
- `WEATHER_SERVER_SETUP.md` - This setup guide

## Integration with Location Server

The weather server can work standalone (with IP-based location) or alongside the location server:

- **Location Server**: Provides location data
- **Weather Server**: Provides weather data (can auto-detect location)

Both can be configured in Claude Desktop simultaneously!
