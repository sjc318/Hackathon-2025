# Quick Start Guide - MCP Location with Real Data

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Run the Demo (Recommended)
```bash
py demo_real_data.py
```

This shows both methods:
1. Direct IP geolocation API
2. MCP server with real location data

## What You'll See

### Real Location Data
- Your actual city, region, and country
- Accurate coordinates with N/S/E/W indicators
- Your timezone and current time
- Your ISP information
- Your IP address

### Example Output
```
[REAL DATA] Your Current Location:
  Location: Cambridge, England, United Kingdom
  Coordinates: 52.1929° N, 0.1256° E
  IP Address: 131.111.184.145
  ISP: Jisc Services Limited
  Timezone: Europe/London
  Current Time: 2025-11-15 21:41:02 GMT
```

## All Available Scripts

| Script | Description |
|--------|-------------|
| `demo_real_data.py` | **Best for testing** - Shows both direct API and MCP methods |
| `test_mcp_complete.py` | Full MCP server + client test |
| `mcp_location_client.py` | MCP client (falls back to direct API) |
| `test_client_direct.py` | Direct IP lookup only (no MCP) |

## How It Works

The code uses **ip-api.com** (free, no API key needed) to get your location based on your IP address. It's automatic and requires no configuration.

## Status Indicators

- `[REAL DATA]` - Successfully retrieved real location
- `[FALLBACK DATA]` - Using mock data (API unavailable)
- `[ERROR]` - Something went wrong

## Need Help?

See [REAL_DATA_SUMMARY.md](REAL_DATA_SUMMARY.md) for complete documentation.
