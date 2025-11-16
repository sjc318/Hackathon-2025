#!/usr/bin/env python3
"""
MCP Location Server for Claude Desktop
This is a stdio-based MCP server that provides location services via JSON-RPC.
"""

import asyncio
import json
import sys
from typing import Any, Dict, Optional
import httpx


class StdioMCPServer:
    """MCP Server that communicates via stdio (for Claude Desktop)"""

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
                        'isp': data.get('isp', 'Unknown'),
                        'ip': data.get('query', 'Unknown')
                    }
                else:
                    raise Exception("API returned error status")
        except Exception as e:
            # Fallback to mock data
            return {
                'city': 'San Francisco',
                'region': 'California',
                'country': 'USA',
                'lat': 37.7749,
                'lon': -122.4194,
                'timezone': 'America/Los_Angeles',
                'isp': 'Unknown',
                'ip': '0.0.0.0',
                'error': str(e)
            }

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "location-mcp-server",
                "version": "1.0.0"
            }
        }

    def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": [
                {
                    "name": "get_location",
                    "description": "Get current location based on IP address (returns real geolocation data)",
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

        if tool_name == "get_location":
            location = await self.get_real_location()

            # Format latitude/longitude
            lat_dir = "N" if location['lat'] >= 0 else "S"
            lon_dir = "E" if location['lon'] >= 0 else "W"

            status = "[REAL DATA]" if 'error' not in location else "[FALLBACK DATA]"
            error_msg = f"\nNote: {location['error']}" if 'error' in location else ""

            text = (
                f"Location: {location['city']}, {location['region']}, {location['country']}\n"
                f"Coordinates: {abs(location['lat']):.4f}° {lat_dir}, {abs(location['lon']):.4f}° {lon_dir}\n"
                f"Timezone: {location['timezone']}\n"
                f"ISP: {location['isp']}\n"
                f"IP Address: {location['ip']}\n"
                f"Status: {status}{error_msg}"
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
        print("MCP Location Server started", file=sys.stderr)

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
    server = StdioMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
