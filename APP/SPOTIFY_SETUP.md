# Spotify Integration Setup Guide

This guide will walk you through setting up real Spotify API integration for the Adaptive Music System.

## Prerequisites

- A Spotify account (Free or Premium)
- Node.js installed (v14 or higher)
- npm or yarn package manager

## Step 1: Register Your Application with Spotify

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the application details:
   - **App Name**: Adaptive Music System (or any name you prefer)
   - **App Description**: AI-powered adaptive music recommendation system
   - **Redirect URI**: `http://localhost:3000/callback`
   - Check the boxes to agree to terms of service
5. Click **"Save"**
6. On your app's dashboard, click **"Settings"**
7. Copy your **Client ID** - you'll need this later
8. Click **"Edit Settings"** and add these Redirect URIs:
   - `http://localhost:3000/callback`
   - `http://localhost:3000`

## Step 2: Configure Environment Variables

1. Copy the `.env.example` file to create a new `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Open the `.env` file and add your Spotify credentials:
   ```
   REACT_APP_SPOTIFY_CLIENT_ID=your_client_id_here
   REACT_APP_REDIRECT_URI=http://localhost:3000/callback
   ```

3. Replace `your_client_id_here` with the Client ID you copied from the Spotify Dashboard

## Step 3: Install Dependencies

Run the following command to install all required packages:

```bash
npm install
```

This will install:
- `react` and `react-dom` - Core React libraries
- `react-scripts` - Build tools for React
- `lucide-react` - Icon library

## Step 4: Run the Application

Start the development server:

```bash
npm start
```

The application will open in your browser at `http://localhost:3000`

## Step 5: Connect to Spotify

1. Click the **"Connect Spotify"** button
2. You'll be redirected to Spotify's login page
3. Log in with your Spotify credentials
4. Authorize the application to access your Spotify data
5. You'll be redirected back to the application

## Step 6: Load Your Music

1. Click **"Load My Playlists"** to fetch your Spotify playlists
2. The system will analyze your music library and extract audio features
3. Wait for the analysis to complete (this may take a minute for large libraries)
4. Once complete, you'll see your music profile with tempo, energy, and genre preferences

## Step 7: Generate Your Adaptive Playlist

1. Optionally, set your current context (weather, location, activity, time of day)
2. Add keywords if you want to filter by specific moods or genres
3. Click **"Generate My Playlist"**
4. Your personalized queue will be created based on your preferences and context

## Features

### Real Spotify Integration
- ✅ OAuth 2.0 authentication with PKCE flow
- ✅ Fetch user's playlists and tracks
- ✅ Analyze audio features (tempo, energy, valence, acousticness)
- ✅ Control playback (requires Spotify Premium)
- ✅ Skip tracks and adaptive queue management

### AI-Powered Recommendations
- Context-aware music selection based on weather, location, activity, and time
- Adaptive skip threshold that learns from your listening behavior
- Similar track recommendations based on audio features
- Keyword-based filtering

### Behavioral Adaptation
- Tracks your skip patterns and completion rates
- Adjusts recommendations based on early skips
- Adds similar tracks when you show high engagement
- Learns your "skip patience" over time

## Playback Control

### Note on Spotify Playback
- **Free Accounts**: The app can generate playlists and analyze your music, but playback control requires Spotify Premium
- **Premium Accounts**: Full playback control is available, including play, pause, and skip functionality

### Using with Spotify Premium
1. Make sure Spotify is open on at least one device
2. The app will attempt to control your active Spotify session
3. Click Play to start playback through Spotify
4. Use Skip to move to the next track in the queue

### Using without Spotify Premium
1. The app will still generate optimized playlists for you
2. You can see the queue and track information
3. Manually play tracks in your Spotify app to enjoy the recommendations

## Troubleshooting

### "Authentication failed" Error
- Make sure your Client ID is correct in the `.env` file
- Verify the Redirect URI in Spotify Dashboard matches exactly: `http://localhost:3000/callback`
- Clear your browser cache and try again

### "Failed to fetch playlists" Error
- Check that you successfully completed the OAuth flow
- Try logging out and reconnecting to Spotify
- Make sure your Spotify account has at least one playlist

### Playback doesn't work
- Spotify Premium is required for playback control
- Make sure Spotify is open and active on at least one device
- Check that you've authorized the playback scopes

### No audio features showing
- This happens if tracks don't have audio analysis data
- Try loading different playlists
- Some very new or obscure tracks may not have audio features available

## API Rate Limits

Spotify has rate limits on API requests:
- The app limits playlist fetching to the first 10 playlists to avoid rate limits
- If you have many playlists, consider using smaller playlists for faster analysis
- Audio features are fetched in batches of 100 tracks

## Privacy & Data

- All authentication is done through Spotify's official OAuth flow
- No passwords are stored by this application
- Access tokens are stored in your browser's localStorage
- The app only requests read access to your playlists and playback control
- No data is sent to external servers (everything runs locally)

## File Structure

```
├── spotify-config.js       # Spotify API configuration and OAuth helpers
├── spotify-service.js      # Service class for all Spotify API calls
├── music-rec-system.jsx    # Main React component with full integration
├── .env                    # Your environment variables (create this)
├── .env.example           # Example environment file
└── package.json           # Dependencies and scripts
```

## Next Steps

Want to enhance the system further? Consider:

1. **Machine Learning**: Integrate TensorFlow.js for more advanced recommendations
2. **Social Features**: Share playlists with friends
3. **External APIs**: Integrate weather APIs for automatic context detection
4. **Mood Detection**: Use facial recognition or biometric data
5. **Collaborative Filtering**: Learn from similar users' preferences

## Support

If you encounter issues:
1. Check the browser console for error messages
2. Verify all environment variables are set correctly
3. Make sure you're using a compatible browser (Chrome, Firefox, Safari, Edge)
4. Check the Spotify Developer Dashboard for any API status issues

## Resources

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotify Authorization Guide](https://developer.spotify.com/documentation/general/guides/authorization-guide/)
- [Audio Features Documentation](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)

---

Enjoy your adaptive music experience! 🎵
