# OAuth Callback Troubleshooting

## Your OAuth Callback is Working! ✅

The callback URL shows:
```
GET /callback?code=...&state=g14z5dti_t9rMe2sq1yscw
```

This means:
- ✅ Spotify authorization successful
- ✅ User approved the app
- ✅ Callback received with authorization code

## Common Issues & Solutions

### Issue 1: "State mismatch" Error

**Cause**: Session not persisting between login and callback

**Solution**:
1. Check Flask secret key is set:
   ```python
   app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
   ```

2. Verify session configuration in backend:
   ```python
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
   app.config['SESSION_COOKIE_SECURE'] = False  # True for HTTPS
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   ```

3. Make sure cookies are enabled in browser

**Quick Fix**:
- Restart the Flask app
- Clear browser cookies for localhost
- Try again

### Issue 2: "Code verifier not found" Error

**Cause**: Session lost between login and callback

**Solution**:
Same as Issue 1 - session persistence problem

### Issue 3: Token Exchange Failed

**Cause**: Invalid client ID or redirect URI mismatch

**Check**:
1. Spotify Dashboard settings match exactly:
   - Redirect URI: `http://localhost:5000/callback` (exact match!)
   - No trailing slash
   - Correct port number

2. `.env` file has correct CLIENT_ID:
   ```env
   SPOTIFY_CLIENT_ID=your_actual_client_id
   SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
   ```

### Issue 4: Callback Shows Error in URL

If you see `?error=...` in callback URL:

- `access_denied` - User clicked "Cancel"
- `invalid_client` - Wrong client ID
- `redirect_uri_mismatch` - Redirect URI doesn't match Spotify settings

## Debugging Steps

### 1. Check Session Persistence

Add this to your backend for debugging:

```python
@app.route('/callback')
def callback():
    # Add debugging
    print(f"[DEBUG] Session has code_verifier: {session.get('code_verifier') is not None}")
    print(f"[DEBUG] Session has oauth_state: {session.get('oauth_state') is not None}")
    print(f"[DEBUG] Callback state: {request.args.get('state')}")

    # ... rest of callback code
```

### 2. Verify Spotify App Settings

1. Go to https://developer.spotify.com/dashboard
2. Click your app
3. Click "Edit Settings"
4. Under "Redirect URIs", verify:
   ```
   http://localhost:5000/callback
   ```
   (Exact match, no variations)

### 3. Test PKCE Flow

Run the test script:
```bash
python test_oauth.py
```

### 4. Check Environment Variables

```bash
# Check .env file exists
dir .env

# Test loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('CLIENT_ID:', os.getenv('SPOTIFY_CLIENT_ID')[:10] if os.getenv('SPOTIFY_CLIENT_ID') else 'NOT SET')"
```

## Working Flow (Reference)

### 1. User Clicks Login
```
Browser → GET /api/auth/login
Backend → Generates code_verifier, code_challenge, state
Backend → Stores code_verifier, state in session
Backend → Returns Spotify auth URL
```

### 2. User Authorizes on Spotify
```
Browser → Redirected to Spotify
User → Clicks "Agree"
Spotify → Redirects to /callback with code and state
```

### 3. Backend Exchanges Code for Token
```
Browser → GET /callback?code=...&state=...
Backend → Retrieves code_verifier from session
Backend → Verifies state matches
Backend → Calls Spotify token endpoint with code and code_verifier
Backend → Receives access_token and refresh_token
Backend → Stores tokens in session
Backend → Redirects to /?auth=success
```

### 4. User is Authenticated
```
Browser → Shows authenticated UI
Frontend → Can make API calls to backend
Backend → Uses stored tokens to call Spotify API
```

## Quick Checklist

Before running:
- [ ] `.env` file exists with SPOTIFY_CLIENT_ID
- [ ] Redirect URI in Spotify dashboard: `http://localhost:5000/callback`
- [ ] Redirect URI in .env: `http://localhost:5000/callback`
- [ ] Flask secret key is set (in .env or auto-generated)
- [ ] Browser cookies enabled
- [ ] Running on port 5000 (`python adaptive_music_backend.py`)

## Test Manually

1. Start backend:
   ```bash
   python adaptive_music_backend.py
   ```

2. Open browser to:
   ```
   http://localhost:5000
   ```

3. Click "Login with Spotify"

4. Check browser console (F12) for errors

5. Check terminal for backend logs

## Expected Logs (Success)

```
[INFO] User clicked login
[INFO] Generated PKCE parameters
[INFO] Stored in session
[INFO] Redirecting to Spotify
[INFO] Callback received
[INFO] Session data found
[INFO] State verified
[INFO] Exchanging code for token
[INFO] Token received
[INFO] Tokens stored in session
[INFO] Redirecting to home
```

## If Still Having Issues

1. Copy the exact error message
2. Check Flask logs in terminal
3. Check browser console (F12 → Console)
4. Verify all checklist items above
5. Try incognito/private browsing mode (fresh session)

## Session Configuration Issues

If sessions aren't working, try this in your backend:

```python
# More permissive session config for development
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)
```

## Success Indicators

When working correctly, you should see:
1. Redirect to Spotify ✓
2. Spotify authorization page ✓
3. Redirect back to localhost ✓
4. URL changes to `/?auth=success` ✓
5. UI shows "Connected to Spotify" ✓
6. Can analyze library and generate playlists ✓

Your OAuth callback is receiving the code correctly - the issue is likely in the token exchange or session persistence!
