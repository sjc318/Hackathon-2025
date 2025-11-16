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


# User Behavior Learning System
class UserBehaviorTracker:
    """Tracks user listening behavior and learns preferences dynamically"""

    def __init__(self):
        # Store in session - in production, use database
        self.genre_scores = {}  # {genre: score_modifier}
        self.skip_threshold = 0.50  # Start at 50% - tracks below this are considered "skipped"
        self.skip_history = []  # List of skip percentages
        self.listening_history = []  # List of {track_id, genre, completion_percentage, timestamp}

    def update_from_session(self, session_data: Dict[str, Any]):
        """Load tracker state from session"""
        if 'behavior_tracker' in session_data:
            data = session_data['behavior_tracker']
            self.genre_scores = data.get('genre_scores', {})
            self.skip_threshold = data.get('skip_threshold', 0.50)
            self.skip_history = data.get('skip_history', [])
            self.listening_history = data.get('listening_history', [])

    def save_to_session(self, session_data: Dict[str, Any]):
        """Save tracker state to session"""
        session_data['behavior_tracker'] = {
            'genre_scores': self.genre_scores,
            'skip_threshold': self.skip_threshold,
            'skip_history': self.skip_history[-50:],  # Keep last 50
            'listening_history': self.listening_history[-100:]  # Keep last 100
        }

    def record_listening_event(self, track_id: str, genres: List[str], completion_percentage: float):
        """
        Record a listening event and update genre preferences

        Args:
            track_id: Spotify track ID
            genres: List of genres for the track
            completion_percentage: How much of the track was played (0.0 to 1.0)
        """
        import datetime

        # Record the event
        self.listening_history.append({
            'track_id': track_id,
            'genres': genres,
            'completion': completion_percentage,
            'timestamp': datetime.datetime.now().isoformat()
        })

        # Determine if this was a skip or full listen
        was_skipped = completion_percentage < self.skip_threshold

        # Update skip history for threshold adjustment
        if was_skipped:
            self.skip_history.append(completion_percentage)
            self._adjust_skip_threshold()

        # Update genre scores based on completion
        for genre in genres:
            if genre not in self.genre_scores:
                self.genre_scores[genre] = 0.0

            # Score adjustment based on completion
            # Full listen (>threshold): +0.1 to +0.2
            # Partial listen (near threshold): +0.0 to +0.1
            # Skip (<threshold): -0.1 to -0.2
            if completion_percentage >= 0.90:
                # Loved it - big boost
                self.genre_scores[genre] += 0.20
            elif completion_percentage >= self.skip_threshold:
                # Liked it - moderate boost
                adjustment = (completion_percentage - self.skip_threshold) / (1.0 - self.skip_threshold) * 0.15
                self.genre_scores[genre] += adjustment
            else:
                # Skipped - penalty
                penalty = (self.skip_threshold - completion_percentage) / self.skip_threshold * 0.20
                self.genre_scores[genre] -= penalty

            # Clamp genre scores to reasonable range [-1.0, 1.0]
            self.genre_scores[genre] = max(-1.0, min(1.0, self.genre_scores[genre]))

        print(f"[BEHAVIOR] Track {track_id[:8]}... completed {completion_percentage:.1%}, genres: {genres}")
        print(f"[BEHAVIOR] Updated genre scores: {self.genre_scores}")

    def _adjust_skip_threshold(self):
        """Dynamically adjust skip threshold based on recent skip patterns"""
        if len(self.skip_history) < 5:
            return  # Need at least 5 skips to adjust

        # Calculate average skip point from last 20 skips
        recent_skips = self.skip_history[-20:]
        avg_skip_point = sum(recent_skips) / len(recent_skips)

        # Adjust threshold to be slightly above average skip point
        # This allows the system to learn if user typically skips at 30% vs 60%
        new_threshold = min(0.80, max(0.20, avg_skip_point + 0.10))

        if abs(new_threshold - self.skip_threshold) > 0.05:
            print(f"[BEHAVIOR] Adjusting skip threshold: {self.skip_threshold:.2f} -> {new_threshold:.2f}")
            self.skip_threshold = new_threshold

    def get_genre_modifier(self, genres: List[str]) -> float:
        """
        Get score modifier for a track based on learned genre preferences

        Returns:
            float: Score modifier between -0.5 and +0.5
        """
        if not genres:
            return 0.0

        # Average the scores of all genres for this track
        total_score = sum(self.genre_scores.get(genre, 0.0) for genre in genres)
        avg_score = total_score / len(genres)

        # Scale to reasonable modifier range (-0.5 to +0.5)
        modifier = avg_score * 0.5

        return modifier


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
                        "country_code": data.get("countryCode", "US"),  # Add country code
                        "source": "ip-geolocation"
                    }
                    print(f"[INFO] Location: {location_data['city']}, {location_data['country']} ({location_data['country_code']})")
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
            "country_code": "US",
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
                timezone = data.get("timezone", "UTC")

                weather_code = current.get("weather_code", 0)
                conditions = WeatherLocationService._get_weather_description(weather_code)

                # Get current time in location's timezone
                from datetime import datetime
                import pytz
                try:
                    tz = pytz.timezone(timezone)
                    local_time = datetime.now(tz)
                    hour = local_time.hour

                    # Determine time of day
                    if 5 <= hour < 12:
                        time_of_day = "morning"
                    elif 12 <= hour < 17:
                        time_of_day = "afternoon"
                    elif 17 <= hour < 21:
                        time_of_day = "evening"
                    else:
                        time_of_day = "night"

                    time_str = local_time.strftime("%I:%M %p")
                except:
                    time_of_day = "afternoon"
                    time_str = "N/A"

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
                    "timezone": timezone,
                    "time_of_day": time_of_day,
                    "local_time": time_str,
                    "source": "open-meteo-api"
                }
                print(f"[INFO] Weather: {weather_data['temperature']}F, {weather_data['conditions']}, {time_of_day} ({time_str})")
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
                        data['temperature'] = float(value.replace('F', '').replace('C', '').strip())
                    elif 'feels like' in key or 'apparent' in key:
                        data['apparent_temperature'] = float(value.replace('F', '').replace('C', '').strip())
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
        elif activity == 'commuting':
            modifiers['energy_boost'] = 0.2
            modifiers['valence_boost'] = 0.3
            modifiers['tempo_boost'] = 0.1
        elif activity == 'studying':
            modifiers['acoustic_boost'] = 0.5
            modifiers['energy_boost'] = -0.3
            modifiers['tempo_boost'] = -0.2
            modifiers['valence_boost'] = 0.1

        # Time of day modifiers
        if time_of_day == 'morning':
            modifiers['energy_boost'] += 0.3
            modifiers['valence_boost'] += 0.3
            modifiers['tempo_boost'] += 0.2
        elif time_of_day == 'afternoon':
            modifiers['energy_boost'] += 0.1
            modifiers['valence_boost'] += 0.2
        elif time_of_day == 'evening':
            modifiers['energy_boost'] -= 0.1
            modifiers['acoustic_boost'] += 0.2
            modifiers['valence_boost'] += 0.1
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
        keywords: List[str],
        behavior_tracker: Optional['UserBehaviorTracker'] = None,
        parameter_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate comprehensive score with learned genre preferences

        Scoring (with increased distinction for better separation):
        - Base preferences: 25%
        - Learned genre preferences: 30% (NEW - permanent factor)
        - Playlist genre matching: +10% (NEW - bonus for matching selected playlists)
        - Weather/context: 25%
        - Keywords: 10%
        - Popularity: 5%
        - Country top bonus: +7% (REDUCED for balanced recommendations)
        Total range: 0.0 to 1.57
        """
        score = 0.0

        # Apply parameter weights (default to 100% if not specified)
        if parameter_weights is None:
            parameter_weights = {}

        weather_weight = parameter_weights.get('weather', 60) / 60.0  # Default 60%, normalize to 1.0
        genre_weight = parameter_weights.get('genre', 100) / 100.0
        mood_weight = parameter_weights.get('mood', 100) / 100.0
        energy_weight = parameter_weights.get('energy', 100) / 100.0
        playlist_weight = parameter_weights.get('playlist', 100) / 100.0

        # Base preference matching (25% of score) - INCREASED MULTIPLIERS
        tempo_diff = abs(song.get('tempo', 120) - preferences['avg_tempo'])
        score += (1 - min(tempo_diff / 100, 1.0)) * 0.12  # Increased from 0.08

        score += (1 - abs(song.get('energy', 0.5) - preferences['avg_energy'])) * 0.04

        # INCREASED MOOD (VALENCE) EFFECT from 0.03 to 0.08 (more than doubled) - WEIGHTED
        score += (1 - abs(song.get('valence', 0.5) - preferences['avg_valence'])) * 0.08 * mood_weight

        score += (1 - abs(song.get('acousticness', 0.5) - preferences['avg_acousticness'])) * 0.03
        score += (1 - abs(song.get('danceability', 0.5) - preferences['avg_danceability'])) * 0.03

        # LEARNED GENRE PREFERENCES (30% of score) - NEW PERMANENT FACTOR
        if behavior_tracker:
            # Get genres from track's artists
            track_genres = []
            if 'artists' in song:
                for artist in song.get('artists', []):
                    if isinstance(artist, dict) and 'genres' in artist:
                        track_genres.extend(artist['genres'])

            # Get modifier based on learned preferences - WEIGHTED
            genre_modifier = behavior_tracker.get_genre_modifier(track_genres)
            # Base score 0.15 + learned modifier (-0.5 to +0.5) = range 0.0 to 0.65
            genre_contribution = (0.15 + genre_modifier) * genre_weight
            score += max(0.0, min(0.65 * genre_weight, genre_contribution))  # Clamp to valid range

            if track_genres:
                print(f"[SCORE] {song.get('name', 'Unknown')[:30]}... genres: {track_genres[:3]}, modifier: {genre_modifier:+.3f}")
        else:
            # Fallback to static genre preference
            genre = song.get('genre', 'Unknown')
            genre_score = preferences['genre_preferences'].get(genre, 0) / max(preferences['total_songs'], 1)
            score += genre_score * 0.10

        # PLAYLIST GENRE MATCHING BONUS (+10% for matching selected playlists)
        if 'playlist_genres' in preferences and preferences['playlist_genres']:
            track_genres = []
            if 'artists' in song:
                for artist in song.get('artists', []):
                    if isinstance(artist, dict) and 'genres' in artist:
                        track_genres.extend(artist['genres'])

            # Check if any track genre matches playlist genres
            playlist_genres_set = set(preferences['playlist_genres'])
            matching_genres = set(track_genres) & playlist_genres_set

            if matching_genres:
                # Scale bonus based on how many genres match (max 0.10) - WEIGHTED
                genre_match_ratio = min(len(matching_genres) / max(len(playlist_genres_set), 1), 1.0)
                playlist_bonus = genre_match_ratio * 0.10 * playlist_weight
                score += playlist_bonus

        # Weather and context adaptation (25% of score) - INCREASED MULTIPLIERS
        energy = song.get('energy', 0.5)
        valence = song.get('valence', 0.5)
        tempo = song.get('tempo', 120)
        acousticness = song.get('acousticness', 0.5)
        danceability = song.get('danceability', 0.5)

        # Energy matching - INCREASED from 0.08 to 0.10 - WEIGHTED
        if modifiers['energy_boost'] > 0.2 and energy > 0.7:
            score += 0.10 * energy_weight * weather_weight
        elif modifiers['energy_boost'] < -0.2 and energy < 0.4:
            score += 0.10 * energy_weight * weather_weight

        # Valence matching - INCREASED from 0.07 to 0.08 - WEIGHTED
        if modifiers['valence_boost'] > 0.2 and valence > 0.7:
            score += 0.08 * weather_weight
        elif modifiers['valence_boost'] < -0.2 and valence < 0.4:
            score += 0.08 * weather_weight

        # Tempo matching - INCREASED from 0.06 to 0.07 - WEIGHTED
        if modifiers['tempo_boost'] > 0.2 and tempo > 130:
            score += 0.07 * weather_weight
        elif modifiers['tempo_boost'] < -0.1 and tempo < 100:
            score += 0.07 * weather_weight

        # Acousticness matching - INCREASED from 0.07 to 0.08 - WEIGHTED
        if modifiers['acoustic_boost'] > 0.3 and acousticness > 0.6:
            score += 0.08 * weather_weight

        # Danceability matching - INCREASED from 0.07 to 0.08 - WEIGHTED
        if modifiers['danceability_boost'] > 0.3 and danceability > 0.7:
            score += 0.08 * weather_weight

        # Keyword matching (10% of score)
        if keywords:
            for keyword in keywords:
                if keyword and (
                    keyword.lower() in song.get('genre', '').lower() or
                    keyword.lower() in song.get('title', '').lower() or
                    keyword.lower() in song.get('artist', '').lower()
                ):
                    score += 0.10
                    break

        # Popularity bonus (5% of score)
        popularity = song.get('popularity', 50)
        score += (popularity / 100) * 0.05

        # Country Top 50 bonus (7% bonus for trending tracks) - REDUCED from 35% to 7%
        if song.get('source') == 'country_top':
            score += 0.07

        return min(score, 1.57)  # Allow scores up to 1.57 for better distinction

    @staticmethod
    def generate_queue(
        tracks: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        weather: Dict[str, Any],
        context: Dict[str, str],
        keywords: List[str],
        queue_size: int = 10,
        behavior_tracker: Optional['UserBehaviorTracker'] = None,
        parameter_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Generate weather-aware adaptive music queue with learned preferences"""
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
                song, preferences, combined_mods, keywords, behavior_tracker, parameter_weights
            )
            scored_songs.append({**song, 'score': score})

        # Sort by score and select diverse top songs
        scored_songs.sort(key=lambda x: x['score'], reverse=True)
        top_songs = scored_songs[:min(20, len(scored_songs))]

        # Add some randomization to top songs for variety
        import random
        random.shuffle(top_songs)

        final_queue = top_songs[:queue_size]

        # Log source distribution
        country_top_count = sum(1 for track in final_queue if track.get('source') == 'country_top')
        user_tracks_count = len(final_queue) - country_top_count
        print(f"[INFO] Final queue composition: {country_top_count} from country top 50, {user_tracks_count} from user playlists")

        return final_queue


# Helper Functions for Enhanced Recommendations
def analyze_playlist_characteristics(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze overall characteristics of selected playlists
    Focuses on genre distribution and mood
    """
    from collections import Counter

    genres = []
    valence_values = []
    energy_values = []

    for track in tracks:
        # Extract genres from artists (if available)
        if 'artists' in track:
            for artist in track['artists']:
                if isinstance(artist, dict) and 'genres' in artist:
                    genres.extend(artist['genres'])

        # Track audio features if available
        if 'valence' in track:
            valence_values.append(track['valence'])
        if 'energy' in track:
            energy_values.append(track['energy'])

    # Count genre frequency
    genre_counter = Counter(genres)
    top_genres = [genre for genre, count in genre_counter.most_common(10)]

    return {
        'top_genres': top_genres,
        'genre_distribution': dict(genre_counter.most_common(10)),
        'avg_valence': sum(valence_values) / len(valence_values) if valence_values else 0.5,
        'avg_energy': sum(energy_values) / len(energy_values) if energy_values else 0.5,
        'total_tracks': len(tracks)
    }


def get_country_top_tracks(service, country_code: str = 'US', limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch trending/popular tracks using Spotify's search and recommendation APIs
    Since top charts playlists are not publicly accessible via API

    NOTE: Spotify's market parameter doesn't override account country restrictions,
    so this function focuses on general trending tracks rather than country-specific ones
    when the user's account is registered in a different country.
    """
    try:
        print(f"[INFO] Searching for trending tracks (target market: {country_code})")

        import datetime
        current_year = datetime.datetime.now().year

        # Country-specific popular artists to seed recommendations
        # This helps get more relevant regional content
        country_artists = {
            'GB': ['Ed Sheeran', 'Dua Lipa', 'Harry Styles', 'Adele', 'Sam Smith'],
            'US': ['Taylor Swift', 'Drake', 'Ariana Grande', 'Post Malone', 'Billie Eilish'],
            'IN': ['Arijit Singh', 'Badshah', 'Neha Kakkar', 'Divine', 'Shreya Ghoshal']
        }

        # Use country-specific artists if available, otherwise use general popular artists
        seed_artists = country_artists.get(country_code, country_artists['US'])

        all_tracks = []
        seen_ids = set()

        # Strategy 1: Search for tracks by popular artists from that region
        print(f"[INFO] Searching for tracks by popular {country_code} artists")
        for artist_name in seed_artists[:3]:  # Try top 3 artists
            try:
                # Search for the artist to get their ID
                artist_search = service._api_request(
                    f'/search?q={artist_name}&type=artist&limit=1'
                )

                if artist_search and 'artists' in artist_search and artist_search['artists']['items']:
                    artist_id = artist_search['artists']['items'][0]['id']

                    # Get the artist's top tracks
                    top_tracks = service._api_request(
                        f'/artists/{artist_id}/top-tracks?market={country_code}'
                    )

                    if top_tracks and 'tracks' in top_tracks:
                        for track in top_tracks['tracks']:
                            if track and track.get('id') and track['id'] not in seen_ids:
                                if track.get('popularity', 0) >= 60:  # Lower threshold for artist-specific tracks
                                    track['source'] = 'country_top'
                                    all_tracks.append(track)
                                    seen_ids.add(track['id'])

                        print(f"[INFO] Added {len(top_tracks['tracks'])} tracks from {artist_name}")

            except Exception as artist_error:
                print(f"[WARN] Failed to get tracks for artist '{artist_name}': {artist_error}")
                continue

        # Strategy 2: Use general trending search queries with high popularity
        search_queries = [
            f'year:{current_year}',
            f'year:{current_year-1}',
            'tag:hipster'
        ]

        for query in search_queries:
            if len(all_tracks) >= limit:
                break

            try:
                search_response = service._api_request(
                    f'/search?q={query}&type=track&limit=50'
                )

                if search_response and 'tracks' in search_response and 'items' in search_response['tracks']:
                    for track in search_response['tracks']['items']:
                        if track and track.get('id') and track['id'] not in seen_ids:
                            if track.get('popularity', 0) >= 75:  # High threshold for general search
                                track['source'] = 'country_top'
                                all_tracks.append(track)
                                seen_ids.add(track['id'])

                                if len(all_tracks) >= limit:
                                    break

            except Exception as search_error:
                print(f"[WARN] Search query '{query}' failed: {search_error}")
                continue

        if len(all_tracks) > 0:
            # Sort by popularity
            all_tracks.sort(key=lambda x: x.get('popularity', 0), reverse=True)
            result_tracks = all_tracks[:limit]
            avg_pop = sum(t.get('popularity', 0) for t in result_tracks) / len(result_tracks)
            print(f"[INFO] Found {len(result_tracks)} trending tracks (avg popularity: {avg_pop:.1f})")
            return result_tracks

        # Strategy 3: Fallback to recommendations API with popular genres
        print(f"[INFO] Using recommendations API fallback")
        popular_genres = ['pop', 'hip-hop', 'rock', 'electronic', 'dance']
        seed_genres = ','.join(popular_genres[:5])

        rec_response = service._api_request(
            f'/recommendations?seed_genres={seed_genres}&limit={limit}&min_popularity=70'
        )

        if rec_response and 'tracks' in rec_response:
            tracks = []
            for track in rec_response['tracks']:
                if track:
                    track['source'] = 'country_top'
                    tracks.append(track)

            if len(tracks) > 0:
                print(f"[INFO] Got {len(tracks)} recommendations via fallback")
                return tracks

        print(f"[WARN] Could not fetch trending tracks")
        return []

    except Exception as e:
        print(f"[ERROR] Failed to get trending tracks: {e}")
        import traceback
        traceback.print_exc()
        return []


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
        playlist_ids = data.get('playlist_ids')
        parameter_weights = data.get('parameter_weights')

        print(f"[INFO] Generating recommendations for activity: {activity}, queue size: {queue_size}")

        # Get tracks from selected playlists or top tracks
        tracks_data = []

        if playlist_ids and len(playlist_ids) > 0:
            print(f"[INFO] Fetching tracks from {len(playlist_ids)} selected playlists...")
            for idx, playlist_id in enumerate(playlist_ids, 1):
                try:
                    print(f"[INFO] Fetching playlist {idx}/{len(playlist_ids)}: {playlist_id}")
                    playlist_tracks = service.get_playlist_tracks(playlist_id, limit=100)

                    if playlist_tracks and 'items' in playlist_tracks:
                        tracks_before = len(tracks_data)
                        # Extract track objects from playlist items
                        for item in playlist_tracks['items']:
                            if item and 'track' in item and item['track']:
                                tracks_data.append(item['track'])

                        tracks_added = len(tracks_data) - tracks_before
                        print(f"[INFO] [OK] Playlist {playlist_id}: Added {tracks_added} tracks (total items: {len(playlist_tracks['items'])})")
                    else:
                        print(f"[WARN] [FAIL] Playlist {playlist_id}: Empty or invalid response")
                        print(f"[DEBUG] Response: {playlist_tracks}")
                except Exception as e:
                    print(f"[ERROR] [FAIL] Failed to fetch playlist {playlist_id}: {e}")
                    import traceback
                    traceback.print_exc()

            print(f"[INFO] === USER PLAYLISTS SUMMARY ===")
            print(f"[INFO] Total tracks retrieved from user playlists: {len(tracks_data)}")

            if len(tracks_data) == 0:
                print(f"[ERROR] No tracks found in any of the {len(playlist_ids)} selected user playlists")
                return jsonify({'error': 'No tracks found in selected user playlists. Please check if the playlists contain tracks.'}), 400
        else:
            # Fallback to top tracks if no playlists selected
            print("[INFO] No playlists selected, using top tracks...")
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

        # Analyze playlist genre characteristics if playlists were selected
        playlist_analysis = None
        if playlist_ids and len(playlist_ids) > 0:
            print("[INFO] Analyzing selected playlists' characteristics...")
            playlist_analysis = analyze_playlist_characteristics(tracks_data)
            print(f"[INFO] Playlist analysis - Genres: {playlist_analysis.get('top_genres', [])[:5]}")

        # Get top tracks from user's country for additional candidates
        country_code = location.get('country_code') if location else 'US'
        print(f"[INFO] === FETCHING COUNTRY TOP TRACKS ===")
        print(f"[INFO] Country: {country_code}")
        try:
            # Get country top tracks as additional candidates
            country_top_tracks = get_country_top_tracks(service, country_code)

            if len(country_top_tracks) > 0:
                print(f"[INFO] [OK] Successfully retrieved {len(country_top_tracks)} country top tracks from {country_code}")
            else:
                print(f"[WARN] [FAIL] No country top tracks retrieved from {country_code}")

            # Combine playlist tracks with country top tracks
            all_candidate_tracks = tracks_data + country_top_tracks
            print(f"[INFO] === COMBINED CANDIDATE POOL ===")
            print(f"[INFO] User playlist tracks: {len(tracks_data)}")
            print(f"[INFO] Country top tracks: {len(country_top_tracks)}")
            print(f"[INFO] Total candidate tracks: {len(all_candidate_tracks)}")
        except Exception as e:
            print(f"[ERROR] [FAIL] Failed to fetch country top tracks: {e}")
            import traceback
            traceback.print_exc()
            all_candidate_tracks = tracks_data
            print(f"[INFO] Using only user playlist tracks: {len(all_candidate_tracks)}")

        # Load behavior tracker from session
        behavior_tracker = UserBehaviorTracker()
        behavior_tracker.update_from_session(session)
        print(f"[BEHAVIOR] Loaded tracker - {len(behavior_tracker.genre_scores)} learned genres, threshold: {behavior_tracker.skip_threshold:.2f}")

        # Learn user preferences from listening history
        print("[INFO] Analyzing user preferences...")
        preferences = WeatherAwareMusicEngine.learn_preferences(tracks_data)

        # Add playlist genre preference to scoring
        if playlist_analysis:
            preferences['playlist_genres'] = playlist_analysis.get('top_genres', [])
            preferences['playlist_mood'] = playlist_analysis.get('avg_valence', 0.5)

        # Generate recommendations
        print("[INFO] Generating weather-aware playlist...")
        time_of_day = weather.get('time_of_day', 'afternoon') if weather else 'afternoon'
        context = {
            'time_of_day': time_of_day,
            'timeOfDay': time_of_day,  # For compatibility with get_context_modifiers
            'activity': activity
        }
        keywords = []  # Can be enhanced with mood/genre keywords
        print(f"[CONTEXT] Activity: {activity}, Time of Day: {time_of_day}")

        recommendations = WeatherAwareMusicEngine.generate_queue(
            all_candidate_tracks,
            preferences,
            weather or {},
            context,
            keywords,
            queue_size,
            behavior_tracker,  # Pass behavior tracker for genre learning
            parameter_weights  # Pass custom parameter weights
        )

        print(f"[INFO] Generated {len(recommendations)} recommendations")
        if parameter_weights:
            print(f"[WEIGHTS] Custom weights applied: {parameter_weights}")

        # Store candidate pool for dynamic expansion
        # Remove already selected tracks from candidate pool
        selected_ids = {r.get('id') for r in recommendations}
        candidate_pool = [t for t in all_candidate_tracks if t.get('id') not in selected_ids]

        # Store essential data in session for re-scoring
        session['current_preferences'] = preferences
        session['current_weather'] = weather or {}
        session['current_context'] = context
        session['current_keywords'] = keywords
        session['current_parameter_weights'] = parameter_weights  # Store weights for re-scoring

        print(f"[INFO] Candidate pool: {len(candidate_pool)} tracks available for expansion")

        return jsonify({
            'recommendations': recommendations,
            'candidate_pool': candidate_pool,
            'weather': weather,
            'location': location,
            'preferences': preferences
        })

    except Exception as e:
        print(f"[ERROR] Failed to generate recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/behavior/track', methods=['POST'])
def record_listening_behavior():
    """Record user listening behavior to learn genre preferences"""
    try:
        data = request.get_json() or {}
        track_id = data.get('track_id')
        genres = data.get('genres', [])
        completion_percentage = data.get('completion_percentage', 0.0)

        if not track_id:
            return jsonify({'error': 'track_id required'}), 400

        # Load behavior tracker from session
        behavior_tracker = UserBehaviorTracker()
        behavior_tracker.update_from_session(session)

        # Record the listening event
        behavior_tracker.record_listening_event(track_id, genres, completion_percentage)

        # Save updated tracker to session
        behavior_tracker.save_to_session(session)

        return jsonify({
            'success': True,
            'genre_scores': behavior_tracker.genre_scores,
            'skip_threshold': behavior_tracker.skip_threshold
        })

    except Exception as e:
        print(f"[ERROR] Failed to record behavior: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations/rescore', methods=['POST'])
def rescore_candidates():
    """Re-score candidate pool with updated user preferences and return next best track"""
    try:
        data = request.get_json() or {}
        candidates = data.get('candidates', [])

        if not candidates:
            return jsonify({'error': 'No candidates provided'}), 400

        # Load stored preferences and context from session
        preferences = session.get('current_preferences')
        weather = session.get('current_weather', {})
        context = session.get('current_context', {})
        keywords = session.get('current_keywords', [])
        parameter_weights = session.get('current_parameter_weights')  # Load parameter weights

        if not preferences:
            return jsonify({'error': 'No preferences found. Please generate a playlist first.'}), 400

        # Load behavior tracker with updated genre preferences
        behavior_tracker = UserBehaviorTracker()
        behavior_tracker.update_from_session(session)

        print(f"[RESCORE] Re-scoring {len(candidates)} candidates with updated preferences")
        print(f"[RESCORE] Learned genres: {len(behavior_tracker.genre_scores)}, skip threshold: {behavior_tracker.skip_threshold:.2f}")
        if parameter_weights:
            print(f"[RESCORE] Using custom weights: {parameter_weights}")

        # Calculate modifiers
        modifiers = WeatherAwareMusicEngine.get_weather_modifiers(weather)

        # Score all candidates
        scored_candidates = []
        for track in candidates:
            score = WeatherAwareMusicEngine.calculate_song_score(
                track,
                preferences,
                modifiers,
                keywords,
                behavior_tracker,
                parameter_weights  # Pass parameter weights
            )
            track['score'] = score
            scored_candidates.append(track)

        # Sort by score and get the highest
        scored_candidates.sort(key=lambda x: x.get('score', 0), reverse=True)

        if scored_candidates:
            next_track = scored_candidates[0]
            print(f"[RESCORE] Next track: {next_track.get('name')} (score: {next_track.get('score', 0):.2f})")

            return jsonify({
                'success': True,
                'next_track': next_track
            })
        else:
            return jsonify({'error': 'No tracks available'}), 400

    except Exception as e:
        print(f"[ERROR] Failed to rescore candidates: {e}")
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


@app.route('/api/user/playlists')
def get_user_playlists():
    """Get user's playlists with proper format"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        print("[INFO] Fetching user playlists...")
        playlists_response = service.get_user_playlists(limit=50)
        print(f"[INFO] Retrieved {len(playlists_response.get('items', []))} playlists")
        return jsonify(playlists_response)
    except Exception as e:
        print(f"[ERROR] Failed to fetch playlists: {e}")
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
