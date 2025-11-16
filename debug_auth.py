#!/usr/bin/env py
"""
Debug Authentication Flow
Check session persistence and token storage
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"

def test_auth_status():
    """Test authentication status endpoint"""
    print("=" * 60)
    print("Testing Authentication Status")
    print("=" * 60)

    # Create session to maintain cookies
    session = requests.Session()

    # 1. Check initial auth status
    print("\n1. Checking initial auth status...")
    response = session.get(f"{BASE_URL}/api/auth/status")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # 2. Check if session cookies are being set
    print(f"\n2. Cookies after auth check: {session.cookies.get_dict()}")

    # 3. Test login endpoint
    print("\n3. Testing login endpoint...")
    response = session.get(f"{BASE_URL}/api/auth/login")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Auth URL present: {bool(data.get('auth_url'))}")
        print(f"   Cookies after login: {session.cookies.get_dict()}")
    else:
        print(f"   Error: {response.text}")

    # 4. Check session persistence
    print("\n4. Checking session persistence...")
    print(f"   Session cookies: {session.cookies.get_dict()}")

    # 5. Check environment variables
    print("\n5. Environment Configuration:")
    print(f"   SPOTIFY_CLIENT_ID: {'Set' if os.getenv('SPOTIFY_CLIENT_ID') else 'NOT SET'}")
    print(f"   SPOTIFY_REDIRECT_URI: {os.getenv('SPOTIFY_REDIRECT_URI', 'NOT SET')}")
    print(f"   FLASK_SECRET_KEY: {'Set' if os.getenv('FLASK_SECRET_KEY') else 'NOT SET'}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_auth_status()
