# Python Version - Adaptive Music System Setup Guide

This is the **Python/Flask** version of the Adaptive Music System with real Spotify API integration.

## 📁 Project Structure

```
├── app.py                      # Flask backend server
├── spotify_service.py          # Spotify API service class
├── templates/
│   └── index.html             # Frontend HTML/JavaScript
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── .env.python.example        # Example environment file
└── PYTHON_SETUP.md           # This file
```

## 🔧 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Spotify account (Free or Premium)

## 🚀 Quick Start

### Step 1: Register Your Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the details:
   - **App Name**: Adaptive Music System
   - **App Description**: AI-powered adaptive music recommendation system
   - **Redirect URI**: `http://localhost:5000/callback`
5. Click **"Save"**
6. Copy your **Client ID** from the app dashboard

### Step 2: Set Up Environment

1. **Copy the example environment file:**
   ```bash
   cp .env.python.example .env
   ```

2. **Edit the `.env` file:**
   ```bash
   # On Windows
   notepad .env

   # On Mac/Linux
   nano .env
   ```

3. **Add your credentials:**
   ```env
   SPOTIFY_CLIENT_ID=your_actual_client_id_here
   SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
   FLASK_SECRET_KEY=generate_a_random_secret_key
   FLASK_DEBUG=True
   PORT=5000
   ```

4. **Generate a secret key** (optional but recommended):
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output and use it as your `FLASK_SECRET_KEY`

### Step 3: Install Dependencies

**Option A - Using pip:**
```bash
pip install -r requirements.txt
```

**Option B - Using virtual environment (recommended):**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### Step 5: Use the System

1. Open your browser and go to `http://localhost:5000`
2. Click **"Connect Spotify"** → Login with your Spotify account
3. Click **"Load My Playlists"** → The system will analyze your music library
4. Set your context (weather, activity, location, time of day)
5. Optionally add keywords (e.g., "chill", "energetic", "rock")
6. Click **"Generate My Playlist"** → Your personalized queue is ready!

## 🎯 Features

### Backend (Python/Flask)
- ✅ RESTful API with Flask
- ✅ OAuth 2.0 with PKCE authentication
- ✅ Session-based token management
- ✅ Complete Spotify Web API integration
- ✅ AI-powered recommendation engine
- ✅ Context-aware music scoring
- ✅ Adaptive queue generation

### Frontend (HTML/JavaScript)
- ✅ Responsive design with Tailwind CSS
- ✅ Real-time activity logging
- ✅ Interactive music queue display
- ✅ Context configuration interface
- ✅ User profile display

### Music Intelligence
- 🎵 Analyzes tempo, energy, valence, and acousticness
- 🎵 Context-based recommendations (weather, activity, time)
- 🎵 Keyword filtering
- 🎵 Genre preference learning
- 🎵 Similarity scoring

## 📊 How It Works

### 1. Authentication Flow
```
User → Click "Connect" → Spotify OAuth → Callback → Token Storage → Authenticated
```

### 2. Library Analysis
```
Load Playlists → Fetch Tracks → Get Audio Features → Learn Preferences → Store in Session
```

### 3. Queue Generation
```
User Preferences + Context + Keywords → Score All Tracks → Sort by Score → Select Top 10 → Return Queue
```

### 4. Scoring Algorithm
```python
score = (
    tempo_similarity * 0.1 +
    energy_similarity * 0.1 +
    valence_similarity * 0.1 +
    acousticness_similarity * 0.1 +
    genre_preference * 0.2 +
    keyword_match * 0.2 +
    context_score * 0.2
)
```

## 🔌 API Endpoints

### Authentication
- `GET /api/auth/login` - Get Spotify authorization URL
- `GET /callback` - OAuth callback handler
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Logout user

### User Data
- `GET /api/user/profile` - Get user profile
- `GET /api/playlists` - Get user's playlists
- `GET /api/playlists/<id>/tracks` - Get playlist tracks

### Music Intelligence
- `POST /api/analyze-library` - Analyze music library and learn preferences
- `POST /api/generate-queue` - Generate adaptive music queue

### Playback Control (Premium Required)
- `POST /api/playback/play` - Start playback
- `POST /api/playback/pause` - Pause playback
- `POST /api/playback/next` - Skip to next track
- `GET /api/playback/current` - Get current playback state

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SPOTIFY_CLIENT_ID` | Your Spotify app client ID | **Required** |
| `SPOTIFY_REDIRECT_URI` | OAuth redirect URI | `http://localhost:5000/callback` |
| `FLASK_SECRET_KEY` | Flask session secret key | Random (generated) |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `PORT` | Server port | `5000` |

### Context Modifiers

The system adjusts recommendations based on context:

**Weather:**
- ☀️ Sunny → +30% valence, +20% energy
- 🌧️ Rainy → +30% acoustic, -20% valence, -20% energy
- ☁️ Cloudy → No change
- 🌙 Clear Night → No change

**Activity:**
- 🏃 Working Out → +50% energy, +40% tempo
- 😌 Relaxing → -30% energy, +40% acoustic
- 🎯 Focusing → +20% acoustic, -10% energy
- 🎉 Partying → No change

**Time of Day:**
- 🌅 Morning → +20% energy, +20% valence
- ☀️ Afternoon → No change
- 🌆 Evening → No change
- 🌙 Night → -20% energy, +20% acoustic

## 🐛 Troubleshooting

### "SPOTIFY_CLIENT_ID must be set" Error
- Make sure you created the `.env` file from `.env.python.example`
- Verify the client ID is correct (no extra spaces)
- Check that the `.env` file is in the same directory as `app.py`

### "Not authenticated" Error
- Your session may have expired - try logging out and back in
- Clear browser cookies and try again
- Check that redirect URI matches exactly: `http://localhost:5000/callback`

### "Failed to load playlists" Error
- Make sure you have at least one playlist in your Spotify account
- Try logging out and reconnecting
- Check browser console for detailed error messages

### Port Already in Use
```bash
# Use a different port
PORT=5001 python app.py

# Or kill the process using port 5000
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On Mac/Linux:
lsof -ti:5000 | xargs kill -9
```

### Import Errors
```bash
# Make sure all dependencies are installed
pip install -r requirements.txt

# If using virtual environment, make sure it's activated
```

## 🔒 Security Notes

- **Session Management**: Uses server-side sessions (tokens never exposed to frontend)
- **PKCE Flow**: OAuth 2.0 with PKCE (no client secret needed)
- **HTTPS**: For production, use HTTPS and update redirect URIs accordingly
- **Secret Key**: Always use a strong random secret key in production
- **CORS**: Currently allows all origins - restrict in production

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### Environment Variables for Production

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_REDIRECT_URI=https://yourdomain.com/callback
FLASK_SECRET_KEY=long_random_secret_key
FLASK_DEBUG=False
PORT=5000
```

### Deployment Platforms

**Heroku:**
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
heroku config:set SPOTIFY_CLIENT_ID=your_id
heroku config:set SPOTIFY_REDIRECT_URI=https://your-app.herokuapp.com/callback
```

**Railway:**
```bash
# railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

**Google Cloud Run / AWS / Azure:**
- Use Dockerfile with gunicorn
- Set environment variables in platform settings
- Update redirect URI to match your domain

## 📚 Code Overview

### spotify_service.py
- Complete Spotify API wrapper
- Handles OAuth authentication
- Manages token refresh
- All API endpoints (playlists, tracks, audio features, playback)

### app.py
- Flask web server
- REST API endpoints
- Session management
- Music recommendation engine
- Context-aware scoring algorithm

### templates/index.html
- Single-page application
- Vanilla JavaScript (no frameworks)
- Tailwind CSS for styling
- Real-time UI updates

## 🎓 Learning Resources

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OAuth 2.0 with PKCE](https://oauth.net/2/pkce/)
- [Audio Features Explained](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)

## 🆚 Python vs JavaScript Version

| Feature | Python Version | JavaScript Version |
|---------|---------------|-------------------|
| Backend | Flask | Node.js/React |
| Frontend | Vanilla JS | React |
| State Management | Server Sessions | React State |
| Deployment | Heroku, Railway | Vercel, Netlify |
| Best For | Backend devs, APIs | Frontend devs, SPAs |

## 📝 Next Steps

Want to extend the system? Try:

1. **Database Integration** - Save user preferences and history
2. **Real-time Playback** - Integrate Spotify Web Playback SDK
3. **Machine Learning** - Use scikit-learn for better recommendations
4. **Social Features** - Share playlists with friends
5. **External APIs** - Integrate real weather and location APIs
6. **Analytics** - Track listening patterns and insights
7. **Mobile App** - Create React Native or Flutter app

## 💬 Support

If you encounter issues:
1. Check the browser console for errors
2. Check the terminal/console where Flask is running
3. Verify all environment variables are set
4. Ensure Spotify app settings are correct
5. Try clearing browser cache and cookies

---

Enjoy your adaptive music experience! 🎵🐍
