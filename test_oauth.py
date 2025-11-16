#!/usr/bin/env python3
"""
Test OAuth Flow Standalone
Use this to debug Spotify OAuth issues
"""

from spotify_service import SpotifyService
import os

# Test configuration
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_client_id_here')
REDIRECT_URI = 'http://localhost:5000/callback'

def test_oauth_flow():
    """Test the OAuth PKCE flow"""

    print("=" * 60)
    print("Testing Spotify OAuth PKCE Flow")
    print("=" * 60)

    # Create service
    service = SpotifyService(CLIENT_ID, REDIRECT_URI)

    # Generate PKCE parameters
    code_verifier = SpotifyService.generate_code_verifier()
    code_challenge = SpotifyService.generate_code_challenge(code_verifier)
    state = "test_state_12345"

    print(f"\n1. Generated PKCE Parameters:")
    print(f"   Code Verifier (length {len(code_verifier)}): {code_verifier[:20]}...")
    print(f"   Code Challenge: {code_challenge[:20]}...")
    print(f"   State: {state}")

    # Get authorization URL
    auth_url = service.get_authorization_url(code_challenge, state)

    print(f"\n2. Authorization URL:")
    print(f"   {auth_url[:100]}...")

    print(f"\n3. Next Steps:")
    print(f"   - Open the URL in a browser")
    print(f"   - Authorize the app")
    print(f"   - You'll be redirected to: {REDIRECT_URI}?code=...&state=...")
    print(f"   - Copy the 'code' parameter from the redirect URL")
    print(f"   - Run: service.exchange_code_for_token(code, code_verifier)")

    print(f"\n4. Session Requirements:")
    print(f"   - Flask session must store: code_verifier, oauth_state")
    print(f"   - State from callback must match oauth_state in session")
    print(f"   - Code verifier must be the same one used to generate challenge")

    print("\n" + "=" * 60)
    print("Configuration Check:")
    print("=" * 60)
    print(f"CLIENT_ID: {'✓ Set' if CLIENT_ID != 'your_client_id_here' else '✗ Not set'}")
    print(f"REDIRECT_URI: {REDIRECT_URI}")
    print(f"Scopes: {', '.join(SpotifyService.SCOPES)}")

    if CLIENT_ID == 'your_client_id_here':
        print("\n⚠ WARNING: Set SPOTIFY_CLIENT_ID environment variable!")
        print("   export SPOTIFY_CLIENT_ID=your_actual_client_id")
        print("   Or create .env file")


if __name__ == "__main__":
    test_oauth_flow()
