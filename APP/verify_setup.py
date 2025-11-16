"""
Verify Spotify Setup Configuration
Run this to check if everything is configured correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and is valid"""
    print("🔍 Checking .env file...")

    env_path = Path('.env')
    if not env_path.exists():
        print("   ❌ .env file not found!")
        print("   💡 Create it by copying: copy .env.python.example .env")
        return False

    print("   ✅ .env file exists")
    return True

def check_environment_variables():
    """Check if environment variables are set"""
    print("\n🔍 Checking environment variables...")

    load_dotenv()

    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    secret_key = os.getenv('FLASK_SECRET_KEY')

    issues = []

    # Check Client ID
    if not client_id:
        print("   ❌ SPOTIFY_CLIENT_ID is not set")
        issues.append("Set SPOTIFY_CLIENT_ID in .env file")
    elif client_id == 'your_client_id_here':
        print("   ❌ SPOTIFY_CLIENT_ID is still the placeholder value")
        issues.append("Replace 'your_client_id_here' with your actual Spotify Client ID")
    elif len(client_id) != 32:
        print(f"   ⚠️  SPOTIFY_CLIENT_ID length is {len(client_id)} (should be 32)")
        print(f"   Current value: {client_id}")
        issues.append("Client ID should be exactly 32 characters")
    else:
        print(f"   ✅ SPOTIFY_CLIENT_ID is set ({client_id[:8]}...)")

    # Check Redirect URI
    if not redirect_uri:
        print("   ❌ SPOTIFY_REDIRECT_URI is not set")
        issues.append("Set SPOTIFY_REDIRECT_URI in .env file")
    elif redirect_uri == 'http://localhost:5000/callback':
        print(f"   ✅ SPOTIFY_REDIRECT_URI is set correctly: {redirect_uri}")
    else:
        print(f"   ⚠️  SPOTIFY_REDIRECT_URI: {redirect_uri}")
        print(f"   💡 Should be: http://localhost:5000/callback")

    # Check Secret Key
    if not secret_key:
        print("   ❌ FLASK_SECRET_KEY is not set")
        issues.append("Set FLASK_SECRET_KEY in .env file")
    elif 'your_secret_key' in secret_key or len(secret_key) < 32:
        print("   ❌ FLASK_SECRET_KEY is placeholder or too short")
        issues.append("Generate a secret key with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    else:
        print(f"   ✅ FLASK_SECRET_KEY is set (length: {len(secret_key)})")

    return len(issues) == 0, issues

def check_required_files():
    """Check if required files exist"""
    print("\n🔍 Checking required files...")

    required_files = {
        'app.py': 'Main Flask application',
        'spotify_service.py': 'Spotify API service',
        'templates/index.html': 'Frontend HTML',
        'requirements.txt': 'Python dependencies',
    }

    all_exist = True
    for file, description in required_files.items():
        if Path(file).exists():
            print(f"   ✅ {file} - {description}")
        else:
            print(f"   ❌ {file} - {description} NOT FOUND")
            all_exist = False

    return all_exist

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking installed packages...")

    required_packages = ['flask', 'flask_cors', 'requests', 'dotenv']
    missing = []

    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\n   💡 Install missing packages: pip install {' '.join(missing)}")
        return False

    return True

def test_spotify_service():
    """Test if Spotify service can be initialized"""
    print("\n🔍 Testing Spotify service initialization...")

    try:
        load_dotenv()
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')

        if not client_id or client_id == 'your_client_id_here':
            print("   ⚠️  Cannot test - Client ID not set")
            return False

        from spotify_service import SpotifyService
        service = SpotifyService(client_id, redirect_uri)
        print("   ✅ Spotify service initialized successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error initializing service: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("📋 NEXT STEPS:")
    print("="*60)
    print("""
1. Go to Spotify Developer Dashboard:
   https://developer.spotify.com/dashboard

2. Click on your app (or create one if you haven't)

3. In Settings, add this Redirect URI:
   http://localhost:5000/callback

   ⚠️  Make sure to click SAVE!

4. Copy your Client ID from the dashboard

5. Edit .env file and paste your Client ID:
   SPOTIFY_CLIENT_ID=paste_your_actual_client_id_here

6. Generate a secret key:
   python -c "import secrets; print(secrets.token_hex(32))"

7. Add the secret key to .env:
   FLASK_SECRET_KEY=paste_generated_secret_here

8. Run the app:
   python app.py

9. Open browser:
   http://localhost:5000
""")

def main():
    """Main verification function"""
    print("="*60)
    print("🎵 Adaptive Music System - Setup Verification")
    print("="*60)

    results = []

    # Check .env file
    results.append(check_env_file())

    # Check environment variables
    env_ok, issues = check_environment_variables()
    results.append(env_ok)

    # Check required files
    results.append(check_required_files())

    # Check dependencies
    results.append(check_dependencies())

    # Test Spotify service
    results.append(test_spotify_service())

    # Summary
    print("\n" + "="*60)
    if all(results):
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\n🚀 You're ready to run the app:")
        print("   python app.py")
        print("\n   Then open: http://localhost:5000")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print("="*60)

        if not env_ok and issues:
            print("\n🔧 Issues to fix:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")

        print_next_steps()

if __name__ == '__main__':
    main()
