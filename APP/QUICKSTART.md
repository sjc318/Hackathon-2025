# Quick Start Guide - Adaptive Music Backend

## ✅ All Files Ready!

Everything is set up and ready to run:

### Files Created/Copied:
- ✅ `spotify_service.py` - Spotify API wrapper
- ✅ `adaptive_music_backend.py` - Flask backend
- ✅ `templates/index.html` - Web interface
- ✅ `.vscode/settings.json` - VS Code config
- ✅ `requirements.txt` - Dependencies

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip install Flask flask-cors python-dotenv requests httpx aiohttp pytz
```

Or:
```bash
pip install -r requirements.txt
```

### Step 2: Create .env File

Create a `.env` file in the project directory:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
FLASK_SECRET_KEY=your_secret_key_here
```

**Get Spotify Client ID:**
1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Copy the Client ID
4. Add redirect URI: `http://localhost:5000/callback`

**Generate Secret Key:**
```bash
py -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Run the Backend

```bash
python adaptive_music_backend.py
```

Then open: http://localhost:5000

## That's It!

The app will:
1. Show login page
2. Connect to Spotify
3. Get your location and weather
4. Analyze your music library
5. Generate weather-aware playlists

## Files Location

All files are in both locations:

**Project Directory:**
```
c:\Users\nanda\OneDrive\Hackathon-2025\
├── adaptive_music_backend.py
├── spotify_service.py
├── templates/
│   └── index.html
├── .env (create this)
└── requirements.txt
```

**Downloads (backup):**
```
c:\Users\nanda\Downloads\
├── adaptive_music_backend.py
├── spotify_service.py
└── templates/
    └── index.html
```

You can run from either location!

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'spotify_service'
**Solution**: Make sure you're running from a directory that has `spotify_service.py`

### Issue: FileNotFoundError: templates/index.html
**Solution**: Already fixed! Templates folder created in both locations.

### Issue: Flask import error in VS Code
**Solution**: Restart VS Code or see [FIX_FLASK_IMPORT.md](FIX_FLASK_IMPORT.md)

### Issue: No SPOTIFY_CLIENT_ID
**Solution**: Create `.env` file (see Step 2 above)

## Next Steps

1. Create Spotify app (if not done)
2. Add `.env` file with credentials
3. Run the backend
4. Open browser to http://localhost:5000
5. Login with Spotify
6. Enjoy weather-aware music!

## Features

- 🎵 Spotify integration
- 🌤️ Weather-aware recommendations
- 📍 Auto location detection
- 🎯 Context-aware playlists (activity, time of day)
- ⚡ Real-time playback control
- 🎨 Beautiful web interface

See [SPOTIFY_BACKEND_SETUP.md](SPOTIFY_BACKEND_SETUP.md) for detailed documentation.
