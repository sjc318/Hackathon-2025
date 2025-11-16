"""
Adaptive Music System - Flask Backend with Weather Integration
AI-powered music recommendation system with Spotify integration and MCP weather/location services
"""

import os
import secrets
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import httpx

from spotify_service import SpotifyService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Session configuration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True when using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

CORS(app, supports_credentials=True)

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:5000/callback')

# MCP configuration
MCP_LOCATION_URL = os.getenv('MCP_LOCATION_URL', 'http://localhost:3000/mcp')
MCP_WEATHER_URL = os.getenv('MCP_WEATHER_URL', 'http://localhost:3001/mcp')

if not SPOTIFY_CLIENT_ID:
    raise ValueError("SPOTIFY_CLIENT_ID must be set in environment variables")


# MCP Client Implementation
class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, server_url: str, client_name: str = "music-client"):
        self.server_url = server_url
        self.client_name = client_name

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with MCP server"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.server_url}/initialize",
                json={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {
                        "name": self.client_name,
                        "version": "1.0.0"
                    }
                }
            )
            return response.json()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool on the MCP server"""
        if arguments is None:
            arguments = {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            return response.json()


# Weather and Location Services
class WeatherLocationService:
    """Service for getting weather and location data via MCP"""

    @staticmethod
    async def get_location() -> Optional[Dict[str, Any]]:
        """Get current location via IP-based geolocation"""
        # Use IP-based location directly (reliable and free)
        try:
            print("[INFO] Getting location via IP geolocation...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://ip-api.com/json/")
                data = response.json()

                if data.get("status") == "success":
                    location_data = {
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "city": data.get("city"),
                        "region": data.get("regionName"),
                        "country": data.get("country"),
                        "source": "ip-geolocation"
                    }
                    print(f"[INFO] Location: {location_data['city']}, {location_data['country']}")
                    return location_data
        except Exception as e:
            print(f"[ERROR] IP location failed: {e}")

        # Default to San Francisco as last resort
        print("[WARN] Using default location: San Francisco")
        return {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "city": "San Francisco",
            "country": "USA",
            "source": "default"
        }

    @staticmethod
    async def get_weather(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Get current weather via Open-Meteo API"""
        # Use Open-Meteo API directly (free and reliable)
        try:
            print(f"[INFO] Getting weather for coordinates: {latitude}, {longitude}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                    "temperature_unit": "fahrenheit",
                    "wind_speed_unit": "mph",
                    "timezone": "auto"
                }
                
                response = await client.get(url, params=params)
                data = response.json()
                current = data.get("current", {})
                
                weather_code = current.get("weather_code", 0)
                conditions = WeatherLocationService._get_weather_description(weather_code)
                
                weather_data = {
                    "temperature": current.get("temperature_2m", 70),
                    "apparent_temperature": current.get("apparent_temperature", 70),
                    "humidity": current.get("relative_humidity_2m", 50),
                    "wind_speed": current.get("wind_speed_10m", 0),
                    "wind_gusts": current.get("wind_gusts_10m", 0),
                    "wind_direction": current.get("wind_direction_10m", 0),
                    "cloud_cover": current.get("cloud_cover", 0),
                    "precipitation": current.get("precipitation", 0),
                    "conditions": conditions,
                    "description": conditions,  # Add description field for frontend
                    "weather_code": weather_code,
                    "source": "open-meteo-api"
                }
                print(f"[INFO] Weather: {weather_data['temperature']}°F, {weather_data['conditions']}")
                return weather_data
        except Exception as e:
            print(f"Weather API fallback failed: {e}")
            return None

    @staticmethod
    def _parse_weather_text(text: str) -> Optional[Dict[str, Any]]:
        """Parse weather information from MCP text response"""
        try:
            data = {}
            lines = text.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'temperature' in key and 'feels' not in key:
                        data['temperature'] = float(value.replace('°F', '').replace('°C', '').strip())
                    elif 'feels like' in key or 'apparent' in key:
                        data['apparent_temperature'] = float(value.replace('°F', '').replace('°C', '').strip())
                    elif 'humidity' in key:
                        data['humidity'] = float(value.replace('%', '').strip())
                    elif 'wind speed' in key:
                        data['wind_speed'] = float(value.replace('mph', '').replace('km/h', '').strip())
                    elif 'cloud' in key:
                        data['cloud_cover'] = float(value.replace('%', '').strip())
                    elif 'precipitation' in key:
                        data['precipitation'] = float(value.replace('mm', '').replace('in', '').strip())
                    elif 'conditions' in key:
                        data['conditions'] = value
            
            return data if data else None
        except Exception as e:
            print(f"Error parsing weather text: {e}")
            return None

    @staticmethod
    def _get_weather_description(weather_code: int) -> str:
        """Convert weather code to description"""
        weather_codes = {
            0: "clear", 1: "clear", 2: "partly_cloudy", 3: "cloudy",
            45: "foggy", 48: "foggy",
            51: "drizzle", 53: "drizzle", 55: "drizzle",
            61: "rainy", 63: "rainy", 65: "rainy",
            71: "snowy", 73: "snowy", 75: "snowy", 77: "snowy",
            80: "rainy", 81: "rainy", 82: "rainy",
            85: "snowy", 86: "snowy",
            95: "stormy", 96: "stormy", 99: "stormy"
        }
        return weather_codes.get(weather_code, "clear")


def get_spotify_service() -> SpotifyService:
    """Get or create Spotify service instance"""
    return SpotifyService(SPOTIFY_CLIENT_ID, SPOTIFY_REDIRECT_URI)


def load_spotify_tokens(service: SpotifyService) -> bool:
    """Load Spotify tokens from session"""
    if 'spotify_tokens' in session:
        tokens = session['spotify_tokens']
        service.set_token_data(
            tokens['access_token'],
            tokens['refresh_token'],
            tokens['expires_in']
        )
        return True
    return False


def save_spotify_tokens(service: SpotifyService) -> None:
    """Save Spotify tokens to session"""
    tokens = service.get_token_data()
    if tokens:
        session['spotify_tokens'] = tokens


# Enhanced Music Recommendation Engine with Weather Integration
class WeatherAwareMusicEngine:
    """Engine for generating weather-aware music recommendations"""

    @staticmethod
    def learn_preferences(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Learn user preferences from tracks"""
        if not tracks:
            return {}

        total = len(tracks)
        avg_tempo = sum(t.get('tempo', 120) for t in tracks) / total
        avg_energy = sum(t.get('energy', 0.5) for t in tracks) / total
        avg_valence = sum(t.get('valence', 0.5) for t in tracks) / total
        avg_acousticness = sum(t.get('acousticness', 0.5) for t in tracks) / total
        avg_danceability = sum(t.get('danceability', 0.5) for t in tracks) / total

        # Count genres
        genre_count = {}
        for track in tracks:
            genre = track.get('genre', 'Unknown')
            genre_count[genre] = genre_count.get(genre, 0) + 1

        return {
            'avg_tempo': avg_tempo,
            'avg_energy': avg_energy,
            'avg_valence': avg_valence,
            'avg_acousticness': avg_acousticness,
            'avg_danceability': avg_danceability,
            'genre_preferences': genre_count,
            'total_songs': total,
        }

    @staticmethod
    def get_weather_modifiers(weather: Dict[str, Any]) -> Dict[str, float]:
        """Get weather-based modifiers for music recommendations"""
        modifiers = {
            'energy_boost': 0.0,
            'valence_boost': 0.0,
            'tempo_boost': 0.0,
            'acoustic_boost': 0.0,
            'danceability_boost': 0.0,
        }

        # Temperature-based modifiers
        temp = weather.get('temperature', 70)
        apparent_temp = weather.get('apparent_temperature', temp)
        
        if apparent_temp < 40:  # Cold weather
            modifiers['energy_boost'] = 0.3  # Energetic music to warm up
            modifiers['tempo_boost'] = 0.2
            modifiers['valence_boost'] = 0.2  # Uplifting music
        elif apparent_temp > 85:  # Hot weather
            modifiers['energy_boost'] = -0.2  # More relaxed music
            modifiers['acoustic_boost'] = 0.2
            modifiers['valence_boost'] = 0.3  # Happy summer vibes
        elif 60 <= apparent_temp <= 75:  # Pleasant weather
            modifiers['valence_boost'] = 0.3
            modifiers['danceability_boost'] = 0.2

        # Cloud cover and precipitation
        cloud_cover = weather.get('cloud_cover', 0)
        precipitation = weather.get('precipitation', 0)
        
        if precipitation > 0.5 or cloud_cover > 70:  # Rainy/cloudy
            modifiers['acoustic_boost'] = 0.4
            modifiers['valence_boost'] = -0.2
            modifiers['energy_boost'] = -0.2
            modifiers['tempo_boost'] = -0.1
        elif cloud_cover < 30:  # Clear skies
            modifiers['valence_boost'] = 0.3
            modifiers['energy_boost'] = 0.2

        # Wind conditions
        wind_speed = weather.get('wind_speed', 0)
        wind_gusts = weather.get('wind_gusts', wind_speed)
        
        if wind_gusts > 25:  # Windy/stormy
            modifiers['energy_boost'] = 0.3
            modifiers['tempo_boost'] = 0.2
        elif wind_speed < 5:  # Calm
            modifiers['acoustic_boost'] = 0.2
            modifiers['energy_boost'] = -0.1

        # Humidity effects
        humidity = weather.get('humidity', 50)
        if humidity > 80:  # Very humid
            modifiers['energy_boost'] = -0.2
            modifiers['tempo_boost'] = -0.1

        # Weather condition overrides
        conditions = weather.get('conditions', '').lower()
        if 'storm' in conditions or 'thunder' in conditions:
            modifiers['energy_boost'] = 0.4
            modifiers['tempo_boost'] = 0.3
            modifiers['acoustic_boost'] = -0.2
        elif 'snow' in conditions:
            modifiers['acoustic_boost'] = 0.3
            modifiers['valence_boost'] = 0.2
            modifiers['energy_boost'] = -0.1

        return modifiers

    @staticmethod
    def get_context_modifiers(context: Dict[str, str]) -> Dict[str, float]:
        """Get context-based modifiers for recommendations"""
        modifiers = {
            'energy_boost': 0.0,
            'valence_boost': 0.0,
            'tempo_boost': 0.0,
            'acoustic_boost': 0.0,
            'danceability_boost': 0.0,
        }

        activity = context.get('activity', 'relaxing')
        time_of_day = context.get('timeOfDay', 'afternoon')

        # Activity modifiers
        if activity == 'working out':
            modifiers['energy_boost'] = 0.5
            modifiers['tempo_boost'] = 0.5
            modifiers['danceability_boost'] = 0.4
        elif activity == 'relaxing':
            modifiers['energy_boost'] = -0.4
            modifiers['acoustic_boost'] = 0.5
            modifiers['tempo_boost'] = -0.2
        elif activity == 'focusing':
            modifiers['acoustic_boost'] = 0.4
            modifiers['energy_boost'] = -0.2
            modifiers['valence_boost'] = 0.1
        elif activity == 'party':
            modifiers['energy_boost'] = 0.6
            modifiers['danceability_boost'] = 0.5
            modifiers['valence_boost'] = 0.4

        # Time of day modifiers
        if time_of_day == 'morning':
            modifiers['energy_boost'] += 0.3
            modifiers['valence_boost'] += 0.3
            modifiers['tempo_boost'] += 0.2
        elif time_of_day == 'night':
            modifiers['energy_boost'] -= 0.3
            modifiers['acoustic_boost'] += 0.3
            modifiers['tempo_boost'] -= 0.1

        return modifiers

    @staticmethod
    def combine_modifiers(weather_mods: Dict[str, float], context_mods: Dict[str, float]) -> Dict[str, float]:
        """Combine weather and context modifiers with appropriate weights"""
        combined = {}
        for key in weather_mods.keys():
            # Weather has 60% weight, context has 40% weight
            combined[key] = (weather_mods[key] * 0.6) + (context_mods[key] * 0.4)
        return combined

    @staticmethod
    def calculate_song_score(
        song: Dict[str, Any],
        preferences: Dict[str, Any],
        modifiers: Dict[str, float],
        keywords: List[str]
    ) -> float:
        """Calculate comprehensive score for a song"""
        score = 0.0

        # Base preference matching (40% of score)
        tempo_diff = abs(song.get('tempo', 120) - preferences['avg_tempo'])
        score += (1 - min(tempo_diff / 100, 1.0)) * 0.08

        score += (1 - abs(song.get('energy', 0.5) - preferences['avg_energy'])) * 0.08
        score += (1 - abs(song.get('valence', 0.5) - preferences['avg_valence'])) * 0.08
        score += (1 - abs(song.get('acousticness', 0.5) - preferences['avg_acousticness'])) * 0.08
        score += (1 - abs(song.get('danceability', 0.5) - preferences['avg_danceability'])) * 0.08

        # Genre preference
        genre = song.get('genre', 'Unknown')
        genre_score = preferences['genre_preferences'].get(genre, 0) / preferences['total_songs']
        score += genre_score * 0.15

        # Weather and context adaptation (35% of score)
        energy = song.get('energy', 0.5)
        valence = song.get('valence', 0.5)
        tempo = song.get('tempo', 120)
        acousticness = song.get('acousticness', 0.5)
        danceability = song.get('danceability', 0.5)

        # Energy matching
        if modifiers['energy_boost'] > 0.2 and energy > 0.7:
            score += 0.08
        elif modifiers['energy_boost'] < -0.2 and energy < 0.4:
            score += 0.08
        
        # Valence matching
        if modifiers['valence_boost'] > 0.2 and valence > 0.7:
            score += 0.07
        elif modifiers['valence_boost'] < -0.2 and valence < 0.4:
            score += 0.07
        
        # Tempo matching
        if modifiers['tempo_boost'] > 0.2 and tempo > 130:
            score += 0.06
        elif modifiers['tempo_boost'] < -0.1 and tempo < 100:
            score += 0.06
        
        # Acousticness matching
        if modifiers['acoustic_boost'] > 0.3 and acousticness > 0.6:
            score += 0.07
        
        # Danceability matching
        if modifiers['danceability_boost'] > 0.3 and danceability > 0.7:
            score += 0.07

        # Keyword matching (15% of score)
        if keywords:
            for keyword in keywords:
                if keyword and (
                    keyword.lower() in song.get('genre', '').lower() or
                    keyword.lower() in song.get('title', '').lower() or
                    keyword.lower() in song.get('artist', '').lower()
                ):
                    score += 0.15
                    break

        # Popularity bonus (10% of score)
        popularity = song.get('popularity', 50)
        score += (popularity / 100) * 0.10

        return min(score, 1.0)

    @staticmethod
    def generate_queue(
        tracks: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        weather: Dict[str, Any],
        context: Dict[str, str],
        keywords: List[str],
        queue_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate weather-aware adaptive music queue"""
        if not tracks or not preferences:
            return []

        # Get modifiers
        weather_mods = WeatherAwareMusicEngine.get_weather_modifiers(weather)
        context_mods = WeatherAwareMusicEngine.get_context_modifiers(context)
        combined_mods = WeatherAwareMusicEngine.combine_modifiers(weather_mods, context_mods)

        # Score each song
        scored_songs = []
        for song in tracks:
            score = WeatherAwareMusicEngine.calculate_song_score(
                song, preferences, combined_mods, keywords
            )
            scored_songs.append({**song, 'score': score})

        # Sort by score and select diverse top songs
        scored_songs.sort(key=lambda x: x['score'], reverse=True)
        top_songs = scored_songs[:min(20, len(scored_songs))]

        # Add some randomization to top songs for variety
        import random
        random.shuffle(top_songs)
        
        return top_songs[:queue_size]


# API Routes
@app.route('/')
def index():
    """Serve main page"""
    try:
        # Try to serve from templates folder first
        return render_template('index.html')
    except:
        # Fallback to serving the file directly
        import os
        html_path = os.path.join(os.path.dirname(__file__), 'index.html')
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                return f.read()
        return "Please place index.html in the same directory as this script or in a templates folder", 404


@app.route('/api/auth/login')
def login():
    """Initiate Spotify OAuth flow"""
    service = get_spotify_service()

    # Generate PKCE parameters
    code_verifier = SpotifyService.generate_code_verifier()
    code_challenge = SpotifyService.generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(16)

    # Store in session
    session['code_verifier'] = code_verifier
    session['oauth_state'] = state

    # Get authorization URL
    auth_url = service.get_authorization_url(code_challenge, state)

    return jsonify({'auth_url': auth_url})


@app.route('/callback')
def callback():
    """Handle OAuth callback from Spotify"""
    print("[DEBUG] Callback endpoint called")
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    print(f"[DEBUG] Code present: {bool(code)}")
    print(f"[DEBUG] State: {state}")
    print(f"[DEBUG] Session oauth_state: {session.get('oauth_state')}")
    print(f"[DEBUG] Session has code_verifier: {bool(session.get('code_verifier'))}")

    if error:
        print(f"[ERROR] OAuth error: {error}")
        return jsonify({'error': error}), 400

    # Verify state
    if state != session.get('oauth_state'):
        print(f"[ERROR] State mismatch! Expected: {session.get('oauth_state')}, Got: {state}")
        return jsonify({'error': 'State mismatch'}), 400

    code_verifier = session.get('code_verifier')
    if not code_verifier:
        print("[ERROR] Code verifier not found in session")
        return jsonify({'error': 'Code verifier not found'}), 400

    try:
        print("[INFO] Exchanging code for token...")
        service = get_spotify_service()
        service.exchange_code_for_token(code, code_verifier)
        print("[INFO] Token exchange successful")

        save_spotify_tokens(service)
        print("[INFO] Tokens saved to session")

        # Clean up session
        session.pop('code_verifier', None)
        session.pop('oauth_state', None)

        # Redirect to frontend
        print("[INFO] Redirecting to /?auth=success")
        return redirect('/?auth=success')
    except Exception as e:
        print(f"[ERROR] Token exchange failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    print("[DEBUG] Auth status check")
    print(f"[DEBUG] Session has spotify_tokens: {bool(session.get('spotify_tokens'))}")
    service = get_spotify_service()
    tokens_loaded = load_spotify_tokens(service)
    print(f"[DEBUG] Tokens loaded: {tokens_loaded}")
    if tokens_loaded:
        is_valid = service.is_token_valid()
        print(f"[DEBUG] Token valid: {is_valid}")
        if is_valid:
            return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.pop('spotify_tokens', None)
    return jsonify({'success': True})


@app.route('/api/auth/token')
def get_token():
    """Get access token for Web Playback SDK"""
    if 'spotify_tokens' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    tokens = session['spotify_tokens']
    return jsonify({'access_token': tokens['access_token']})


@app.route('/api/weather/current')
async def get_current_weather():
    """Get current weather conditions"""
    try:
        # Get location
        location = await WeatherLocationService.get_location()
        if not location:
            return jsonify({'error': 'Could not determine location'}), 500

        # Get weather
        weather = await WeatherLocationService.get_weather(
            location['latitude'],
            location['longitude']
        )
        
        if not weather:
            return jsonify({'error': 'Could not fetch weather data'}), 500

        return jsonify({
            'location': location,
            'weather': weather
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations/generate', methods=['POST'])
async def generate_recommendations():
    """Generate weather-aware music recommendations"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get request parameters
        data = request.get_json() or {}
        activity = data.get('activity', 'relaxing')
        queue_size = min(data.get('queue_size', 10), 50)  # Max 50 tracks

        print(f"[INFO] Generating recommendations for activity: {activity}, queue size: {queue_size}")

        # Get user's top tracks for analysis
        print("[INFO] Fetching user's top tracks from Spotify...")
        top_tracks = service.get_user_top_tracks(limit=50)
        if not top_tracks or 'items' not in top_tracks:
            return jsonify({'error': 'Could not fetch user listening history'}), 500

        tracks_data = top_tracks['items']
        print(f"[INFO] Retrieved {len(tracks_data)} top tracks")

        # Get weather and location
        print("[INFO] Getting current weather...")
        location = await WeatherLocationService.get_location()
        weather = await WeatherLocationService.get_weather(
            location['latitude'],
            location['longitude']
        ) if location else None

        # Learn user preferences from listening history
        print("[INFO] Analyzing user preferences...")
        preferences = WeatherAwareMusicEngine.learn_preferences(tracks_data)

        # Generate recommendations
        print("[INFO] Generating weather-aware playlist...")
        context = {
            'time_of_day': 'afternoon',  # Can be enhanced with actual time
            'activity': activity
        }
        keywords = []  # Can be enhanced with mood/genre keywords

        recommendations = WeatherAwareMusicEngine.generate_queue(
            tracks_data,
            preferences,
            weather or {},
            context,
            keywords,
            queue_size
        )

        print(f"[INFO] Generated {len(recommendations)} recommendations")

        return jsonify({
            'recommendations': recommendations,
            'weather': weather,
            'location': location,
            'preferences': preferences
        })

    except Exception as e:
        print(f"[ERROR] Failed to generate recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/profile')
def get_profile():
    """Get user profile"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        profile = service.get_user_profile()
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlists')
def get_playlists():
    """Get user's playlists"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        playlists = service.get_all_user_playlists()
        return jsonify({'playlists': playlists})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze-library', methods=['POST'])
def analyze_library():
    """Analyze user's music library"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get playlists
        playlists = service.get_all_user_playlists()[:10]

        # Collect all tracks
        all_tracks = []
        for playlist in playlists:
            tracks = service.get_all_playlist_tracks(playlist['id'])
            all_tracks.extend([item['track'] for item in tracks if item.get('track')])

        # Remove duplicates
        unique_tracks = {track['id']: track for track in all_tracks if track.get('id')}.values()
        unique_tracks = list(unique_tracks)

        # Get audio features
        track_ids = [track['id'] for track in unique_tracks]
        audio_features = service.get_audio_features(track_ids)

        # Combine track data with audio features
        tracks_with_features = []
        for track, features in zip(unique_tracks, audio_features):
            if features:
                tracks_with_features.append({
                    'id': track['id'],
                    'title': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'genre': track.get('genres', ['Unknown'])[0] if track.get('genres') else 'Unknown',
                    'tempo': features.get('tempo', 120),
                    'energy': features.get('energy', 0.5),
                    'valence': features.get('valence', 0.5),
                    'acousticness': features.get('acousticness', 0.5),
                    'danceability': features.get('danceability', 0.5),
                    'duration': track['duration_ms'] / 1000,
                    'spotify_uri': track['uri'],
                    'album_art': track['album']['images'][0]['url'] if track['album'].get('images') else None,
                    'popularity': track.get('popularity', 50),
                })

        # Learn preferences
        preferences = WeatherAwareMusicEngine.learn_preferences(tracks_with_features)

        # Store in session
        session['tracks'] = tracks_with_features
        session['preferences'] = preferences

        return jsonify({
            'tracks': tracks_with_features,
            'preferences': preferences,
            'total_tracks': len(tracks_with_features),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-queue', methods=['POST'])
async def generate_queue_route():
    """Generate weather-aware adaptive music queue"""
    data = request.json
    context = data.get('context', {})
    keywords = data.get('keywords', '').split(',')
    keywords = [k.strip() for k in keywords if k.strip()]

    # Get tracks and preferences from session
    tracks = session.get('tracks', [])
    preferences = session.get('preferences', {})

    if not tracks or not preferences:
        return jsonify({'error': 'No library data. Please analyze your library first.'}), 400

    try:
        # Get current location
        location = await WeatherLocationService.get_location()
        if not location:
            return jsonify({'error': 'Could not determine location'}), 500

        # Get current weather
        weather = await WeatherLocationService.get_weather(
            location['latitude'],
            location['longitude']
        )
        
        if not weather:
            return jsonify({'error': 'Could not fetch weather data'}), 500

        # Generate queue with weather awareness
        queue = WeatherAwareMusicEngine.generate_queue(
            tracks,
            preferences,
            weather,
            context,
            keywords,
            queue_size=10
        )

        return jsonify({
            'queue': queue,
            'weather': weather,
            'location': location
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playback/play', methods=['POST'])
def play():
    """Start playback"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.json
    uris = data.get('uris', [])

    try:
        service.play(uris=uris)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playback/pause', methods=['POST'])
def pause():
    """Pause playback"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        service.pause()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playback/next', methods=['POST'])
def next_track():
    """Skip to next track"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        service.skip_to_next()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playback/current')
def current_playback():
    """Get current playback state"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        playback = service.get_current_playback()
        return jsonify(playback if playback else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
