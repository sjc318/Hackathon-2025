#!/usr/bin/env python3
"""
Complete demonstration of MCP Location Services with REAL DATA
Shows both MCP server approach and direct API fallback
"""

import asyncio
import httpx
from aiohttp import web
from datetime import datetime
import pytz


async def demonstrate_direct_location():
    """Direct API call to get real location data"""
    print("\n" + "=" * 70)
    print("METHOD 1: Direct IP Geolocation API Call")
    print("=" * 70 + "\n")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://ip-api.com/json/")
            data = response.json()

            if data.get('status') == 'success':
                lat = data.get('lat', 0)
                lon = data.get('lon', 0)
                lat_dir = "N" if lat >= 0 else "S"
                lon_dir = "E" if lon >= 0 else "W"

                print("[REAL DATA] Your Current Location:")
                print(f"  Location: {data.get('city')}, {data.get('regionName')}, {data.get('country')}")
                print(f"  Coordinates: {abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}")
                print(f"  IP Address: {data.get('query')}")
                print(f"  ISP: {data.get('isp')}")
                print(f"  Timezone: {data.get('timezone')}")

                # Get timezone details
                tz = pytz.timezone(data.get('timezone', 'UTC'))
                now = datetime.now(tz)
                print(f"  Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"  UTC Offset: {now.strftime('%z')}")

                return data
            else:
                print("[ERROR] API returned unsuccessful status")
                return None

    except Exception as e:
        print(f"[ERROR] Failed to get location: {e}")
        return None


async def demonstrate_mcp_server():
    """Demonstrate MCP server with real location data"""
    print("\n" + "=" * 70)
    print("METHOD 2: MCP Server with Real Location Data")
    print("=" * 70 + "\n")

    # Define simple MCP server handlers
    async def initialize(request):
        return web.json_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "real-location-mcp-server",
                "version": "1.0.0"
            }
        })

    async def list_tools(request):
        return web.json_response({
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get real location based on IP address",
                    "inputSchema": {"type": "object", "properties": {}}
                },
                {
                    "name": "get_timezone",
                    "description": "Get detailed timezone information",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        })

    async def call_tool(request):
        data = await request.json()
        tool_name = data.get("name")

        if tool_name == "get_location":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get("http://ip-api.com/json/")
                    location_data = response.json()

                if location_data.get('status') == 'success':
                    lat = location_data.get('lat', 0)
                    lon = location_data.get('lon', 0)
                    lat_dir = "N" if lat >= 0 else "S"
                    lon_dir = "E" if lon >= 0 else "W"

                    text = (
                        f"Location: {location_data.get('city')}, {location_data.get('regionName')}, {location_data.get('country')}\n"
                        f"Coordinates: {abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}\n"
                        f"Timezone: {location_data.get('timezone')}\n"
                        f"ISP: {location_data.get('isp')}\n"
                        f"IP: {location_data.get('query')}\n"
                        f"Status: [REAL DATA]"
                    )
                else:
                    text = "Error: Could not retrieve location"
            except Exception as e:
                text = f"Error: {e}"

            return web.json_response({
                "content": [{"type": "text", "text": text}]
            })

        elif tool_name == "get_timezone":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get("http://ip-api.com/json/")
                    location_data = response.json()

                if location_data.get('status') == 'success':
                    tz = pytz.timezone(location_data.get('timezone', 'UTC'))
                    now = datetime.now(tz)
                    utc_offset = now.strftime('%z')
                    utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}"

                    text = (
                        f"Timezone: {location_data.get('timezone')}\n"
                        f"UTC Offset: {utc_offset_formatted}\n"
                        f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                        f"DST Active: {'Yes' if bool(now.dst()) else 'No'}\n"
                        f"Status: [REAL DATA]"
                    )
                else:
                    text = "Error: Could not retrieve timezone"
            except Exception as e:
                text = f"Error: {e}"

            return web.json_response({
                "content": [{"type": "text", "text": text}]
            })

        return web.json_response({"error": "Unknown tool"}, status=400)

    # Setup server
    app = web.Application()
    app.router.add_post('/mcp/initialize', initialize)
    app.router.add_post('/mcp/tools/list', list_tools)
    app.router.add_post('/mcp/tools/call', call_tool)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3002)  # Use different port
    await site.start()
    print(f"[SERVER] MCP server started on http://localhost:3002")

    # Test the server with a client
    await asyncio.sleep(0.5)

    try:
        async with httpx.AsyncClient() as client:
            # Initialize
            print("\n[CLIENT] Connecting to MCP server...")
            init_response = await client.post(
                "http://localhost:3002/mcp/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "demo-client", "version": "1.0.0"}
                }
            )
            server_info = init_response.json()
            print(f"[CLIENT] Connected to: {server_info.get('serverInfo', {}).get('name')}")

            # List tools
            print("\n[CLIENT] Requesting available tools...")
            tools_response = await client.post(
                "http://localhost:3002/mcp/tools/list",
                json={}
            )
            tools = tools_response.json().get("tools", [])
            print(f"[CLIENT] Found {len(tools)} tools")

            # Call get_location
            print("\n[CLIENT] Calling 'get_location' tool...")
            location_response = await client.post(
                "http://localhost:3002/mcp/tools/call",
                json={"name": "get_location", "arguments": {}}
            )
            result = location_response.json()
            print("\n--- Location Data from MCP ---")
            for item in result.get("content", []):
                if item.get("type") == "text":
                    print(item.get("text"))

            # Call get_timezone
            print("\n[CLIENT] Calling 'get_timezone' tool...")
            tz_response = await client.post(
                "http://localhost:3002/mcp/tools/call",
                json={"name": "get_timezone", "arguments": {}}
            )
            result = tz_response.json()
            print("\n--- Timezone Data from MCP ---")
            for item in result.get("content", []):
                if item.get("type") == "text":
                    print(item.get("text"))

    finally:
        await runner.cleanup()
        print("\n[SERVER] MCP server stopped")


async def main():
    print("\n" + "=" * 70)
    print("REAL LOCATION DATA DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows two ways to get REAL location data:")
    print("1. Direct IP geolocation API call")
    print("2. MCP server that provides real location data")
    print("=" * 70)

    # Method 1: Direct API
    await demonstrate_direct_location()

    # Method 2: MCP Server
    await demonstrate_mcp_server()

    print("\n" + "=" * 70)
    print("[SUCCESS] Both methods demonstrated with REAL DATA")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
