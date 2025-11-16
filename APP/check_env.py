"""
Quick script to check what environment variables Flask will read
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("="*60)
print("📂 Checking Environment Configuration")
print("="*60)

# Check current directory
print(f"\n📍 Current directory: {os.getcwd()}")

# Check for .env files
print("\n📄 Looking for .env files:")
env_files = ['.env', '.env.python.example', '.env.local', '.env.development']
for file in env_files:
    if Path(file).exists():
        print(f"   ✅ Found: {file}")
    else:
        print(f"   ❌ Not found: {file}")

# Load .env
print("\n🔄 Loading .env file...")
load_dotenv()

# Check what was loaded
print("\n🔑 Environment variables loaded:")
client_id = os.getenv('SPOTIFY_CLIENT_ID')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
secret_key = os.getenv('FLASK_SECRET_KEY')

if client_id:
    if client_id == 'your_client_id_here':
        print(f"   ⚠️  SPOTIFY_CLIENT_ID: {client_id} (STILL PLACEHOLDER!)")
    else:
        masked = client_id[:4] + '*' * (len(client_id) - 8) + client_id[-4:] if len(client_id) > 8 else '***'
        print(f"   ✅ SPOTIFY_CLIENT_ID: {masked} (length: {len(client_id)})")
else:
    print(f"   ❌ SPOTIFY_CLIENT_ID: Not set!")

if redirect_uri:
    print(f"   ✅ SPOTIFY_REDIRECT_URI: {redirect_uri}")
else:
    print(f"   ❌ SPOTIFY_REDIRECT_URI: Not set!")

if secret_key:
    if 'your_secret_key' in secret_key:
        print(f"   ⚠️  FLASK_SECRET_KEY: (STILL PLACEHOLDER!)")
    else:
        print(f"   ✅ FLASK_SECRET_KEY: Set (length: {len(secret_key)})")
else:
    print(f"   ⚠️  FLASK_SECRET_KEY: Not set (will use random key)")

# Summary
print("\n" + "="*60)
print("📋 SUMMARY")
print("="*60)

issues = []

if not Path('.env').exists():
    issues.append("❌ .env file doesn't exist! Create it with: copy .env.python.example .env")

if not client_id or client_id == 'your_client_id_here':
    issues.append("❌ SPOTIFY_CLIENT_ID not set correctly")

if client_id and len(client_id) != 32:
    issues.append(f"❌ SPOTIFY_CLIENT_ID wrong length ({len(client_id)} instead of 32)")

if not redirect_uri:
    issues.append("❌ SPOTIFY_REDIRECT_URI not set")

if issues:
    print("\n🚨 ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print("\n💡 FIX:")
    print("   1. Make sure .env file exists (not .env.python.example)")
    print("   2. Edit .env with: notepad .env")
    print("   3. Add your actual Spotify Client ID")
    print("   4. Restart Flask: python app.py")
else:
    print("\n✅ Configuration looks good!")
    print("   If you still get 'invalid client', the issue is in Spotify Dashboard.")
    print("\n   Next steps:")
    print("   1. Go to: https://developer.spotify.com/dashboard")
    print("   2. Verify the Client ID matches")
    print("   3. Add redirect URI and click SAVE")

print("="*60)
