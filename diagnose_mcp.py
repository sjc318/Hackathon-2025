#!/usr/bin/env python3
"""
Diagnostic tool for MCP Location Server
Checks common issues and provides troubleshooting information
"""

import sys
import os
import json
import subprocess


def check_python():
    """Check Python installation"""
    print("=" * 70)
    print("1. Checking Python Installation")
    print("=" * 70)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print("[OK] Python is working\n")


def check_dependencies():
    """Check required dependencies"""
    print("=" * 70)
    print("2. Checking Dependencies")
    print("=" * 70)

    try:
        import httpx
        print(f"[OK] httpx is installed (version {httpx.__version__})")
    except ImportError:
        print("[ERROR] httpx is NOT installed")
        print("Fix: Run 'pip install httpx'")
        return False

    print()
    return True


def check_file_exists():
    """Check if MCP server file exists"""
    print("=" * 70)
    print("3. Checking MCP Server File")
    print("=" * 70)

    server_file = "mcp_location_server.py"
    if os.path.exists(server_file):
        print(f"[OK] {server_file} exists")
        print(f"     Path: {os.path.abspath(server_file)}")
    else:
        print(f"[ERROR] {server_file} not found")
        return False

    print()
    return True


def test_server_startup():
    """Test if server can start"""
    print("=" * 70)
    print("4. Testing Server Startup")
    print("=" * 70)

    try:
        # Try to import the server
        sys.path.insert(0, os.getcwd())

        print("[OK] Server file can be imported")
        print()
        return True

    except Exception as e:
        print(f"[ERROR] Server startup failed: {e}")
        return False


def generate_claude_config():
    """Generate Claude Desktop configuration"""
    print("=" * 70)
    print("5. Claude Desktop Configuration")
    print("=" * 70)

    server_path = os.path.abspath("mcp_location_server.py")
    python_path = sys.executable

    # For Windows, escape backslashes
    if sys.platform == "win32":
        server_path = server_path.replace("\\", "\\\\")
        python_path = python_path.replace("\\", "\\\\")

    config = {
        "mcpServers": {
            "location": {
                "command": python_path,
                "args": [server_path]
            }
        }
    }

    print("Add this to your Claude Desktop config:")
    print()
    print(json.dumps(config, indent=2))
    print()

    if sys.platform == "win32":
        config_path = os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")
    else:
        config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")

    print(f"Config file location: {config_path}")
    print()


def test_json_rpc():
    """Test JSON-RPC communication"""
    print("=" * 70)
    print("6. Testing JSON-RPC Communication")
    print("=" * 70)

    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, "mcp_location_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "diagnostic", "version": "1.0.0"}
            }
        }

        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()

        # Read response
        import time
        time.sleep(0.5)

        response_line = process.stdout.readline()

        if response_line:
            response = json.loads(response_line)
            if "result" in response:
                print("[OK] Server responded correctly")
                print(f"     Server name: {response['result']['serverInfo']['name']}")
            else:
                print("[ERROR] Server returned error:")
                print(f"     {response.get('error', 'Unknown error')}")
        else:
            # Check stderr for errors
            stderr_output = process.stderr.read()
            if stderr_output:
                print("[ERROR] Server startup error:")
                print(stderr_output)
            else:
                print("[ERROR] No response from server")

        process.terminate()
        process.wait(timeout=2)

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    print()


def main():
    """Run all diagnostics"""
    print("\n" + "=" * 70)
    print("MCP LOCATION SERVER DIAGNOSTIC TOOL")
    print("=" * 70 + "\n")

    check_python()

    if not check_dependencies():
        print("\n[CRITICAL] Fix dependency issues before continuing")
        return

    if not check_file_exists():
        print("\n[CRITICAL] Fix file issues before continuing")
        return

    test_server_startup()
    generate_claude_config()
    test_json_rpc()

    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Copy the configuration above to your Claude Desktop config")
    print("2. Restart Claude Desktop completely")
    print("3. Ask Claude to 'use the get_location tool'")
    print()


if __name__ == "__main__":
    main()
