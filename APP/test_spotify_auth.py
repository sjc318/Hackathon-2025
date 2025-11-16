"""
Test Spotify OAuth URL Generation
This will show you the exact URL being generated and help debug issues
"""

import os
from dotenv import load_dotenv
from spotify_service import SpotifyService

print("="*80)
print("Testing Spotify OAuth Configuration")
print("="*80)

# Load environment
load_dotenv()

client_id = os.getenv('SPOTIFY_CLIENT_ID')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

print("\nCurrent Configuration:")
if client_id and len(client_id) > 12:
    print(f"   Client ID: {client_id[:8]}...{client_id[-4:]}")
else:
    print(f"   Client ID: ERROR - Too short or missing")
print(f"   Redirect URI: {redirect_uri}")

# Initialize service
service = SpotifyService(client_id, redirect_uri)

# Generate PKCE parameters
code_verifier = SpotifyService.generate_code_verifier()
code_challenge = SpotifyService.generate_code_challenge(code_verifier)
state = "test_state_123"

# Generate authorization URL
auth_url = service.get_authorization_url(code_challenge, state)

print("\nGenerated Authorization URL:")
print(f"   {auth_url}")

# Parse the URL to show components
from urllib.parse import urlparse, parse_qs

parsed = urlparse(auth_url)
params = parse_qs(parsed.query)

print("\nURL Components:")
print(f"   Base URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
print(f"   Parameters:")
for key, value in params.items():
    if key == 'client_id':
        print(f"      - {key}: {value[0][:8]}...{value[0][-4:]}")
    elif key == 'code_challenge':
        print(f"      - {key}: {value[0][:20]}... (truncated)")
    else:
        print(f"      - {key}: {value[0]}")

print("\n" + "="*80)
print("Manual Test Instructions:")
print("="*80)
print("""
1. Copy the full authorization URL above
2. Paste it into your browser
3. Try to access it

Expected Results:
[GOOD] You see Spotify login page or app authorization page
[BAD]  You see "Invalid client" error

If you see "Invalid client":
  -> The Client ID in your .env doesn't match Spotify Dashboard
  -> Double-check you copied the correct Client ID

If you see "Invalid redirect URI":
  -> The redirect URI in your .env isn't whitelisted
  -> Go to Spotify Dashboard -> Settings -> Redirect URIs
  -> Add exactly: """ + str(redirect_uri) + """
  -> Click SAVE!

If you see Spotify login page:
  [OK] Your configuration is correct!
  -> The issue might be with Flask session or callback handling
""")

print("\n" + "="*80)
print("Checklist:")
print("="*80)

checklist = [
    "Client ID is 32 characters long",
    "Client ID matches Spotify Dashboard (no typos)",
    "Redirect URI matches what's in Spotify Dashboard Settings",
    "You clicked 'Save' in Spotify Dashboard after adding redirect URI",
    "No quotes around values in .env file",
    "No spaces before/after = in .env file",
    "Restarted Flask app after changing .env"
]

for item in checklist:
    print(f"   [ ] {item}")

print("\n" + "="*80)
print("Next Steps:")
print("="*80)
print("""
1. Manually test the URL above in your browser
2. Go to Spotify Dashboard and verify settings:
   https://developer.spotify.com/dashboard
3. If still having issues, check the error message carefully
""")

print("="*80)
