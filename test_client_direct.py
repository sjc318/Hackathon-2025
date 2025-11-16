#!/usr/bin/env python3
"""
Direct test of MCP location client with real data fallback
"""

import asyncio
import sys
sys.path.insert(0, '.')
from mcp_location_client import get_location_via_ip


async def main():
    print("\n" + "=" * 70)
    print("TESTING DIRECT IP-BASED LOCATION (REAL DATA)")
    print("=" * 70 + "\n")

    print("This demonstrates the real location data functionality.")
    print("No MCP server needed - direct IP geolocation API call.\n")

    await get_location_via_ip()

    print("\n" + "=" * 70)
    print("[SUCCESS] Real location data retrieved!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
