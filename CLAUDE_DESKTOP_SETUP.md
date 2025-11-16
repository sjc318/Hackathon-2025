# Setting up Location MCP Server with Claude Desktop

This guide shows you how to integrate the Location MCP server with Claude Desktop.

## Prerequisites

1. Python 3.7+ installed
2. Required Python packages installed:
   ```bash
   pip install httpx
   ```

## Configuration

### Step 1: Locate Claude Desktop Config File

The Claude Desktop config file is located at:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Step 2: Add MCP Server Configuration

Open the config file and add the location server to the `mcpServers` section:

```json
{
  "mcpServers": {
    "location": {
      "command": "python",
      "args": [
        "c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_location_server.py"
      ]
    }
  }
}
```

**Important Notes:**
- Use **double backslashes** (`\\`) in Windows paths
- Replace the path with your actual file location
- If you have other MCP servers configured, add this as another entry

### Step 3: Restart Claude Desktop

After saving the config file, completely quit and restart Claude Desktop.

## Testing the MCP Server

Once configured, you can test it in Claude Desktop by asking:

- "What is my current location?"
- "Get my location using the location tool"
- "Use the get_location tool"

Claude will use the MCP server to fetch your real IP-based location.

## Example Response

When working correctly, you'll get a response like:

```
Location: Cambridge, England, United Kingdom
Coordinates: 52.1929° N, 0.1256° E
Timezone: Europe/London
ISP: Jisc Services Limited
IP Address: 131.111.184.145
Status: [REAL DATA]
```

## Troubleshooting

### Server Not Showing Up

1. Check the config file path is correct
2. Verify Python is in your PATH: `python --version`
3. Check Claude Desktop logs at:
   - Windows: `%APPDATA%\Claude\logs`
   - macOS: `~/Library/Logs/Claude`

### Import Errors

If you get import errors, install dependencies:
```bash
pip install httpx
```

Or use the full Python path in the config:
```json
{
  "mcpServers": {
    "location": {
      "command": "C:\\Users\\nanda\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": [
        "c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_location_server.py"
      ]
    }
  }
}
```

### Debugging

You can test the server directly from command line:
```bash
python mcp_location_server.py
```

Then type (as a single line):
```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}
```

Press Enter. You should get a JSON response.

## How It Works

1. **Stdio Communication**: The MCP server uses stdin/stdout for JSON-RPC communication
2. **IP Geolocation**: Uses ip-api.com to get real location data based on IP address
3. **Tool Interface**: Exposes a `get_location` tool that Claude can call
4. **Real Data**: Returns actual geolocation information, not mock data

## API Used

This server uses the free ip-api.com service:
- No API key required
- Rate limit: 45 requests/minute
- Returns: city, region, country, coordinates, timezone, ISP, IP address
