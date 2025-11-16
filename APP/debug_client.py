"""
Debug "Invalid Client" Error
Run this to diagnose Spotify Client ID issues
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("="*60)
print("🔍 DEBUGGING 'INVALID CLIENT' ERROR")
print("="*60)

# Check 1: Does .env file exist?
print("\n1️⃣ Checking for .env file...")
env_file = Path('.env')
if env_file.exists():
    print(f"   ✅ Found .env file at: {env_file.absolute()}")

    # Show file contents (masked)
    print("\n   📄 File contents (Client ID masked):")
    with open('.env', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'CLIENT_ID' in line and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip()
                if value and value != 'your_client_id_here':
                    # Mask the client ID
                    masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                    print(f"   {key}={masked}")
                else:
                    print(f"   {line.strip()} ⚠️ STILL PLACEHOLDER!")
            else:
                print(f"   {line.strip()}")
else:
    print(f"   ❌ .env file NOT FOUND!")
    print(f"   💡 Create it with: copy .env.python.example .env")
    exit(1)

# Check 2: Load environment variables
print("\n2️⃣ Loading environment variables...")
load_dotenv()

client_id = os.getenv('SPOTIFY_CLIENT_ID')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

# Check 3: Validate Client ID
print("\n3️⃣ Validating SPOTIFY_CLIENT_ID...")

if not client_id:
    print("   ❌ SPOTIFY_CLIENT_ID is not set or is empty!")
    print("   💡 Add this to .env: SPOTIFY_CLIENT_ID=your_actual_client_id")
    exit(1)

if client_id == 'your_client_id_here':
    print("   ❌ SPOTIFY_CLIENT_ID is still the placeholder value!")
    print("   💡 Replace with your actual Client ID from Spotify Dashboard")
    print("   🔗 Get it from: https://developer.spotify.com/dashboard")
    exit(1)

# Check length
print(f"   Client ID length: {len(client_id)}")
if len(client_id) != 32:
    print(f"   ⚠️  WARNING: Client ID should be 32 characters, but is {len(client_id)}")
    print(f"   💡 Double-check you copied the Client ID (not Client Secret)")
else:
    print("   ✅ Client ID length is correct (32 characters)")

# Check for common issues
issues = []

if ' ' in client_id:
    issues.append("Contains spaces")
if '"' in client_id or "'" in client_id:
    issues.append("Contains quotes")
if '\n' in client_id or '\r' in client_id:
    issues.append("Contains newlines")
if client_id.startswith(' ') or client_id.endswith(' '):
    issues.append("Has leading/trailing whitespace")

if issues:
    print(f"   ⚠️  Issues found: {', '.join(issues)}")
    print(f"   Client ID (repr): {repr(client_id)}")
else:
    print("   ✅ No formatting issues detected")

# Mask and show
masked = client_id[:8] + '*' * (len(client_id) - 12) + client_id[-4:]
print(f"   Client ID (masked): {masked}")

# Check 4: Validate Redirect URI
print("\n4️⃣ Validating SPOTIFY_REDIRECT_URI...")

if not redirect_uri:
    print("   ❌ SPOTIFY_REDIRECT_URI is not set!")
    exit(1)

print(f"   Redirect URI: {redirect_uri}")

expected_uri = "http://10.248.152.7:5000/callback"
if redirect_uri == expected_uri:
    print(f"   ✅ Matches expected: {expected_uri}")
else:
    print(f"   ⚠️  Expected: {expected_uri}")
    print(f"   ⚠️  Got:      {redirect_uri}")

# Check 5: Test if Spotify service can be initialized
print("\n5️⃣ Testing Spotify service initialization...")

try:
    from spotify_service import SpotifyService
    service = SpotifyService(client_id, redirect_uri)
    print("   ✅ Spotify service initialized successfully")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Check 6: Show what to check in Spotify Dashboard
print("\n6️⃣ Spotify Dashboard Checklist:")
print("   Go to: https://developer.spotify.com/dashboard")
print("   Click on your app, then Settings")
print()
print("   ✓ Client ID should match:")
print(f"     {masked}")
print()
print("   ✓ Redirect URIs should include:")
print(f"     {redirect_uri}")
print()
print("   ✓ Make sure you clicked 'Save' after adding the redirect URI!")

# Summary
print("\n" + "="*60)
print("📋 SUMMARY")
print("="*60)

if client_id and client_id != 'your_client_id_here' and len(client_id) == 32 and redirect_uri:
    print("✅ Configuration looks correct!")
    print()
    print("If you're still getting 'invalid client', the issue is likely:")
    print()
    print("1. 🔍 Client ID doesn't match Spotify Dashboard")
    print("   → Double-check you copied the correct Client ID")
    print("   → Make sure you're looking at the right app")
    print()
    print("2. 🔍 Redirect URI not saved in Spotify Dashboard")
    print(f"   → Add this exactly: {redirect_uri}")
    print("   → Click 'Save' in Spotify Dashboard")
    print()
    print("3. 🔍 Using Client Secret instead of Client ID")
    print("   → Use the 'Client ID' (visible by default)")
    print("   → Don't use 'Client Secret' (hidden, requires clicking)")
    print()
    print("4. 🔍 Wrong Spotify app")
    print("   → Make sure you're using the correct app in dashboard")
    print()
    print("Next steps:")
    print("  1. Restart Flask: python app.py")
    print("  2. Try connecting: http://10.248.152.7:5000")
    print("  3. Click 'Connect Spotify'")
else:
    print("⚠️  Configuration has issues - see errors above")

print("="*60)
