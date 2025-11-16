# SOLUTION: Fix Your Claude Desktop Config

## The Problem

Your Claude Desktop config is pointing to `mcp_location_client.py` (the CLIENT), but it needs to point to `mcp_location_server.py` (the SERVER).

The errors show:
```
'run', 'mcp_location_client.py'   <-- WRONG FILE!
```

## The Fix

Open your Claude Desktop config file at:
```
C:\Users\nanda\AppData\Roaming\Claude\claude_desktop_config.json
```

**Change it to this:**

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

**Key changes:**
1. Use `python.exe` instead of `uv.exe`
2. Point to `mcp_location_server.py` NOT `mcp_location_client.py`
3. Use full path to Python executable

## Alternative (if using uv)

If you want to use `uv`, the config should be:

```json
{
  "mcpServers": {
    "location": {
      "command": "C:\\Users\\nanda\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\nanda\\OneDrive\\Hackathon-2025",
        "run",
        "mcp_location_server.py"
      ]
    }
  }
}
```

Notice: `mcp_location_server.py` NOT `mcp_location_client.py`

## After Fixing

1. Save the config file
2. Completely quit Claude Desktop (not just close window)
3. Restart Claude Desktop
4. Ask Claude: "use the get_location tool"

The errors should be gone!
