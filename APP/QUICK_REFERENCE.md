# MCP Servers - Quick Reference

## For Claude Desktop - USE THESE FILES

### Location Server
```
File: mcp_location_server.py
Test: python test_mcp_stdio.py
```

### Weather Server
```
File: mcp_weather_server.py
Test: python test_weather_server.py
```

## Claude Desktop Config

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "location": {
      "command": "C:\\Users\\nanda\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_location_server.py"]
    },
    "weather": {
      "command": "C:\\Users\\nanda\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
      "args": ["c:\\Users\\nanda\\OneDrive\\Hackathon-2025\\mcp_weather_server.py"]
    }
  }
}
```

## DO NOT Use These with Claude Desktop

❌ `mcp_location_client.py` - HTTP client (for testing only)
❌ `mcp_weather_client.py` - HTTP client (for testing only)

These print text to stdout and cause JSON parsing errors.

## Common Issues & Fixes

### Issue: "Unexpected token" errors in Claude Desktop logs
**Fix**: You're using the CLIENT instead of SERVER
- Change: `mcp_location_client.py` → `mcp_location_server.py`
- Change: `mcp_weather_client.py` → `mcp_weather_server.py`

### Issue: Flask import not resolved in VS Code
**Fix**:
1. Restart VS Code (`.vscode/settings.json` created)
2. Or: Ctrl+Shift+P → "Python: Select Interpreter" → Select Python 3.13

### Issue: Git error with 'nul' file
**Fix**: File is now in `.gitignore`, just don't commit it

### Issue: Merge conflicts
**Fix**: Already resolved in `.gitignore` and `requirements.txt`

## Files Overview

### Servers (stdio-based, for Claude Desktop)
- `mcp_location_server.py` ✅
- `mcp_weather_server.py` ✅

### Clients (HTTP-based, for testing)
- `mcp_location_client.py` - Fixed import issue ✅
- `mcp_weather_client.py` - Emoji-free ✅

### Test Scripts
- `test_mcp_stdio.py` - Test location server
- `test_weather_server.py` - Test weather server
- `diagnose_mcp.py` - Diagnostic tool

### Documentation
- `CLAUDE_DESKTOP_SETUP.md` - Location server setup
- `WEATHER_SERVER_SETUP.md` - Weather server setup
- `FIX_CONFIG.md` - Fix common config error
- `MCP_SERVERS_SUMMARY.md` - Complete overview
- `MCP_CLIENT_PROBLEMS_FIXED.md` - Client fixes
- `FIX_FLASK_IMPORT.md` - Fix Flask import in VS Code
- `QUICK_REFERENCE.md` - This file

## Testing

### Test Servers
```bash
python test_mcp_stdio.py      # Location
python test_weather_server.py # Weather
```

### Test Flask Backend
```bash
python adaptive_music_backend.py
```

### Check Installations
```bash
py -m pip list | findstr -i "flask httpx aiohttp"
```

## Dependencies

```bash
pip install httpx aiohttp pytz Flask flask-cors python-dotenv
```

Or:
```bash
pip install -r requirements.txt
```

## Quick Setup Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Test servers**: Run test scripts above
3. **Configure Claude Desktop**: Update config file
4. **Restart Claude Desktop**: Completely quit and reopen
5. **Test in Claude**: Ask "What's my location?" or "What's the weather?"

## Need Help?

- Location issues → [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)
- Weather issues → [WEATHER_SERVER_SETUP.md](WEATHER_SERVER_SETUP.md)
- Flask issues → [FIX_FLASK_IMPORT.md](FIX_FLASK_IMPORT.md)
- Client issues → [MCP_CLIENT_PROBLEMS_FIXED.md](MCP_CLIENT_PROBLEMS_FIXED.md)
- Complete guide → [MCP_SERVERS_SUMMARY.md](MCP_SERVERS_SUMMARY.md)
