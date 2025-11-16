# Spotify Adaptive Music Backend - Setup Guide

## Files Overview

### ✅ Already Available

1. **`spotify_service.py`** - Spotify API wrapper (already in project)
   - Handles OAuth 2.0 with PKCE
   - Provides methods for playlists, tracks, playback, audio features
   - Token management and refresh

2. **`adaptive_music_backend.py`** - Flask backend (just copied to project)
   - Weather-aware music recommendation engine
   - Integrates with MCP location and weather services
   - Spotify authentication and playback control

## Prerequisites

### 1. Install Dependencies

```bash
pip install Flask flask-cors python-dotenv requests httpx aiohttp pytz
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Create Spotify App

1. Go to https://developer.spotify.com/dashboard
2. Click "Create an App"
3. Fill in app details:
   - App name: "Adaptive Music System"
   - Description: "Weather-aware music recommendations"
4. Click "Create"
5. Note your **Client ID**
6. Click "Edit Settings"
7. Add Redirect URI: `http://localhost:5000/callback`
8. Save

### 3. Environment Configuration

Create `.env` file in project root:

```env
# Spotify Configuration
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_REDIRECT_URI=http://localhost:5000/callback

# Flask Configuration
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_DEBUG=True
PORT=5000

# MCP Servers (optional - will fall back to IP-based if not available)
MCP_LOCATION_URL=http://localhost:3000/mcp
MCP_WEATHER_URL=http://localhost:3001/mcp
```

Generate a secret key:
```bash
py -c "import secrets; print(secrets.token_hex(32))"
```

## Running the Backend

### Option 1: Direct Run

```bash
python adaptive_music_backend.py
```

### Option 2: With Flask CLI

```bash
set FLASK_APP=adaptive_music_backend.py
flask run
```

Server will start at: `http://localhost:5000`

## API Endpoints

### Authentication
- `GET /api/auth/login` - Start Spotify OAuth
- `GET /callback` - OAuth callback
- `GET /api/auth/status` - Check auth status
- `POST /api/auth/logout` - Logout

### User
- `GET /api/user/profile` - Get user profile
- `GET /api/playlists` - Get user's playlists
- `POST /api/analyze-library` - Analyze music library

### Weather
- `GET /api/weather/current` - Get current weather

### Music Recommendations
- `POST /api/generate-queue` - Generate weather-aware playlist

### Playback Control
- `POST /api/playback/play` - Start playback
- `POST /api/playback/pause` - Pause playback
- `POST /api/playback/next` - Next track
- `GET /api/playback/current` - Current playback state

## How It Works

### 1. Weather-Aware Recommendations

The system analyzes:
- **Temperature**: Affects energy and tempo preferences
- **Weather conditions**: Rain = acoustic, Storm = energetic
- **Cloud cover**: Sunny = upbeat, Cloudy = mellow
- **Wind**: Calm = relaxed, Windy = energetic
- **Humidity**: High humidity = lower energy

### 2. Context Awareness

User context includes:
- **Activity**: working out, relaxing, focusing, party
- **Time of day**: morning, afternoon, evening, night

### 3. Music Features Analyzed

- **Tempo**: Beats per minute
- **Energy**: Intensity and activity
- **Valence**: Musical positivity
- **Acousticness**: Acoustic vs. electronic
- **Danceability**: How suitable for dancing

### 4. MCP Integration

- **Location Service**: Auto-detects user location via IP
- **Weather Service**: Fetches current weather conditions
- **Fallbacks**: Works even if MCP servers aren't running

## Testing the Backend

### 1. Test Import

```bash
python -c "from spotify_service import SpotifyService; print('OK')"
python -c "import adaptive_music_backend; print('OK')"
```

### 2. Test Weather Endpoint

```bash
# Start the backend
python adaptive_music_backend.py

# In another terminal
curl http://localhost:5000/api/weather/current
```

### 3. Test with Frontend

1. Create an HTML file or use the provided frontend
2. Navigate to `http://localhost:5000`
3. Click "Login with Spotify"
4. Authorize the app
5. Analyze your library
6. Generate weather-aware playlist

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'spotify_service'

**Solution**: Make sure `spotify_service.py` is in the same directory
```bash
# Check if file exists
dir spotify_service.py
```

### Issue: Flask import not resolved in VS Code

**Solution**: See [FIX_FLASK_IMPORT.md](FIX_FLASK_IMPORT.md)
- Restart VS Code
- Or select correct Python interpreter

### Issue: SPOTIFY_CLIENT_ID not set

**Solution**: Create `.env` file with your Spotify credentials

### Issue: Spotify OAuth redirect_uri_mismatch

**Solution**: Make sure redirect URI in `.env` matches Spotify app settings exactly:
- In Spotify Dashboard: `http://localhost:5000/callback`
- In `.env`: `http://localhost:5000/callback`

### Issue: Weather/Location not working

**Solution**:
- Start MCP servers if you have them
- Or backend will fall back to IP-based location (works automatically)

## Architecture

```
adaptive_music_backend.py
├── Uses spotify_service.py for Spotify API
├── Uses MCP servers for weather/location (with fallbacks)
├── Analyzes user's music library
├── Generates weather-aware recommendations
└── Provides REST API for frontend
```

## Security Notes

- Never commit `.env` file to Git (already in `.gitignore`)
- Use strong random secret key for Flask sessions
- Spotify tokens are stored in session (server-side only)
- PKCE flow provides additional OAuth security

## Next Steps

1. Install dependencies
2. Create Spotify app and get Client ID
3. Configure `.env` file
4. Run the backend
5. Build or use a frontend to interact with API
6. Enjoy weather-aware music recommendations!

## Files Created

- ✅ `spotify_service.py` - Already exists
- ✅ `adaptive_music_backend.py` - Copied from Downloads
- ✅ `.vscode/settings.json` - VS Code Python config
- ✅ `requirements.txt` - Python dependencies

## Example Request Flow

1. User clicks "Login" → `/api/auth/login`
2. Redirected to Spotify → User authorizes
3. Callback received → `/callback` → Tokens stored
4. User clicks "Analyze Library" → `/api/analyze-library`
5. Backend fetches playlists and audio features
6. User clicks "Generate Playlist" → `/api/generate-queue`
7. Backend gets weather, analyzes context
8. Returns personalized, weather-aware playlist
9. User clicks "Play" → `/api/playback/play`
10. Music starts playing on Spotify!
