#!/usr/bin/env python3
"""
Test script for the stdio-based MCP server
This simulates how Claude Desktop communicates with the MCP server
"""

import asyncio
import json
import subprocess
import sys


async def test_mcp_server():
    """Test the MCP server by sending JSON-RPC requests"""

    print("=" * 70)
    print("Testing MCP Location Server (stdio mode)")
    print("=" * 70)

    # Start the MCP server as a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "mcp_location_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    def send_request(request_id: int, method: str, params: dict = None):
        """Send a JSON-RPC request to the server"""
        if params is None:
            params = {}

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        request_json = json.dumps(request) + "\n"
        print(f"\n[REQUEST {request_id}] {method}")
        print(f"Sending: {request_json.strip()}")

        server_process.stdin.write(request_json)
        server_process.stdin.flush()

        # Read response
        response_line = server_process.stdout.readline()
        print(f"Received: {response_line.strip()}")

        if response_line:
            response = json.loads(response_line)
            return response
        return None

    try:
        # Give server time to start
        await asyncio.sleep(0.5)

        # Test 1: Initialize
        print("\n" + "=" * 70)
        print("TEST 1: Initialize")
        print("=" * 70)
        response = send_request(1, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })

        if response and "result" in response:
            server_info = response["result"].get("serverInfo", {})
            print(f"[OK] Connected to: {server_info.get('name')} v{server_info.get('version')}")
        else:
            print("[ERROR] Initialize failed")
            return

        # Test 2: List tools
        print("\n" + "=" * 70)
        print("TEST 2: List Tools")
        print("=" * 70)
        response = send_request(2, "tools/list")

        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"[OK] Found {len(tools)} tool(s):")
            for tool in tools:
                print(f"  - {tool['name']}: {tool.get('description')}")
        else:
            print("[ERROR] List tools failed")
            return

        # Test 3: Call get_location tool
        print("\n" + "=" * 70)
        print("TEST 3: Call get_location Tool")
        print("=" * 70)
        response = send_request(3, "tools/call", {
            "name": "get_location",
            "arguments": {}
        })

        if response and "result" in response:
            content = response["result"].get("content", [])
            print("\n[OK] Location Data:")
            print("-" * 70)
            for item in content:
                if item.get("type") == "text":
                    print(item.get("text"))
            print("-" * 70)
        else:
            print("[ERROR] Call tool failed")
            if response and "error" in response:
                print(f"Error: {response['error']}")

        print("\n" + "=" * 70)
        print("[SUCCESS] All tests completed")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        server_process.terminate()
        try:
            server_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("\n[INFO] Server stopped")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
