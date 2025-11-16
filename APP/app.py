"""
Adaptive Music System - Flask Backend
AI-powered music recommendation system with Spotify integration
"""

import os
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
from dotenv import load_dotenv

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

if not SPOTIFY_CLIENT_ID:
    raise ValueError("SPOTIFY_CLIENT_ID must be set in environment variables")


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


# Music Recommendation Logic
class MusicRecommendationEngine:
    """Engine for generating adaptive music recommendations"""

    @staticmethod
    def learn_preferences(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn user preferences from tracks

        Args:
            tracks: List of tracks with audio features

        Returns:
            User preference profile
        """
        if not tracks:
            return {}

        total = len(tracks)
        avg_tempo = sum(t.get('tempo', 120) for t in tracks) / total
        avg_energy = sum(t.get('energy', 0.5) for t in tracks) / total
        avg_valence = sum(t.get('valence', 0.5) for t in tracks) / total
        avg_acousticness = sum(t.get('acousticness', 0.5) for t in tracks) / total

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
            'genre_preferences': genre_count,
            'total_songs': total,
        }

    @staticmethod
    def get_context_modifiers(context: Dict[str, str]) -> Dict[str, float]:
        """Get context-based modifiers for recommendations"""
        modifiers = {
            'energy_boost': 0.0,
            'valence_boost': 0.0,
            'tempo_boost': 0.0,
            'acoustic_boost': 0.0,
        }

        weather = context.get('weather', 'sunny')
        activity = context.get('activity', 'relaxing')
        time_of_day = context.get('timeOfDay', 'afternoon')

        # Weather modifiers
        if weather == 'rainy':
            modifiers['acoustic_boost'] = 0.3
            modifiers['valence_boost'] = -0.2
            modifiers['energy_boost'] = -0.2
        elif weather == 'sunny':
            modifiers['valence_boost'] = 0.3
            modifiers['energy_boost'] = 0.2

        # Activity modifiers
        if activity == 'working out':
            modifiers['energy_boost'] = 0.5
            modifiers['tempo_boost'] = 0.4
        elif activity == 'relaxing':
            modifiers['energy_boost'] = -0.3
            modifiers['acoustic_boost'] = 0.4
        elif activity == 'focusing':
            modifiers['acoustic_boost'] = 0.2
            modifiers['energy_boost'] = -0.1

        # Time of day modifiers
        if time_of_day == 'morning':
            modifiers['energy_boost'] += 0.2
            modifiers['valence_boost'] += 0.2
        elif time_of_day == 'night':
            modifiers['energy_boost'] -= 0.2
            modifiers['acoustic_boost'] += 0.2

        return modifiers

    @staticmethod
    def calculate_context_score(song: Dict[str, Any], modifiers: Dict[str, float]) -> float:
        """Calculate how well a song matches the context"""
        score = 0.0

        energy = song.get('energy', 0.5)
        valence = song.get('valence', 0.5)
        tempo = song.get('tempo', 120)
        acousticness = song.get('acousticness', 0.5)

        if modifiers['energy_boost'] > 0 and energy > 0.7:
            score += 0.3
        if modifiers['energy_boost'] < 0 and energy < 0.4:
            score += 0.3
        if modifiers['valence_boost'] > 0 and valence > 0.7:
            score += 0.2
        if modifiers['valence_boost'] < 0 and valence < 0.5:
            score += 0.2
        if modifiers['tempo_boost'] > 0 and tempo > 120:
            score += 0.3
        if modifiers['acoustic_boost'] > 0 and acousticness > 0.6:
            score += 0.3

        return min(score, 1.0)

    @staticmethod
    def calculate_similarity(song1: Dict[str, Any], song2: Dict[str, Any]) -> float:
        """Calculate similarity between two songs"""
        similarity = 0.0

        if song1.get('genre') == song2.get('genre'):
            similarity += 0.3

        similarity += (1 - abs(song1.get('energy', 0.5) - song2.get('energy', 0.5))) * 0.2
        similarity += (1 - abs(song1.get('valence', 0.5) - song2.get('valence', 0.5))) * 0.2
        similarity += (1 - abs(song1.get('tempo', 120) - song2.get('tempo', 120)) / 150) * 0.15
        similarity += (1 - abs(song1.get('acousticness', 0.5) - song2.get('acousticness', 0.5))) * 0.15

        return similarity

    @staticmethod
    def generate_queue(
        tracks: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        context: Dict[str, str],
        keywords: List[str],
        queue_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate adaptive music queue

        Args:
            tracks: Available tracks with audio features
            preferences: User preference profile
            context: Current context (weather, activity, etc.)
            keywords: Keyword filters
            queue_size: Number of tracks to return

        Returns:
            List of recommended tracks
        """
        if not tracks or not preferences:
            return []

        context_modifiers = MusicRecommendationEngine.get_context_modifiers(context)

        # Score each song
        scored_songs = []
        for song in tracks:
            score = 0.0

            # Tempo similarity
            tempo_diff = abs(song.get('tempo', 120) - preferences['avg_tempo'])
            score += (1 - tempo_diff / 150) * 0.1

            # Energy similarity
            score += (1 - abs(song.get('energy', 0.5) - preferences['avg_energy'])) * 0.1

            # Valence similarity
            score += (1 - abs(song.get('valence', 0.5) - preferences['avg_valence'])) * 0.1

            # Acousticness similarity
            score += (1 - abs(song.get('acousticness', 0.5) - preferences['avg_acousticness'])) * 0.1

            # Genre preference
            genre = song.get('genre', 'Unknown')
            genre_score = preferences['genre_preferences'].get(genre, 0) / preferences['total_songs']
            score += genre_score * 0.2

            # Keyword matching
            if keywords:
                for keyword in keywords:
                    if keyword and (
                        keyword.lower() in song.get('genre', '').lower() or
                        keyword.lower() in song.get('title', '').lower() or
                        keyword.lower() in song.get('artist', '').lower()
                    ):
                        score += 0.2
                        break

            # Context score
            score += MusicRecommendationEngine.calculate_context_score(song, context_modifiers) * 0.2

            scored_songs.append({**song, 'score': score})

        # Sort by score and return top songs
        scored_songs.sort(key=lambda x: x['score'], reverse=True)
        top_songs = scored_songs[:min(15, len(scored_songs))]

        # Shuffle top songs and return queue_size
        import random
        random.shuffle(top_songs)
        return top_songs[:queue_size]


# API Routes
@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


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
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return jsonify({'error': error}), 400

    # Verify state
    if state != session.get('oauth_state'):
        return jsonify({'error': 'State mismatch'}), 400

    code_verifier = session.get('code_verifier')
    if not code_verifier:
        return jsonify({'error': 'Code verifier not found'}), 400

    try:
        service = get_spotify_service()
        print(f"[DEBUG] Exchanging code for token...")
        print(f"[DEBUG] Client ID: {SPOTIFY_CLIENT_ID[:8]}...{SPOTIFY_CLIENT_ID[-4:]}")
        print(f"[DEBUG] Redirect URI: {SPOTIFY_REDIRECT_URI}")
        print(f"[DEBUG] Code: {code[:20]}...")

        service.exchange_code_for_token(code, code_verifier)
        save_spotify_tokens(service)

        # Clean up session
        session.pop('code_verifier', None)
        session.pop('oauth_state', None)

        print(f"[DEBUG] Token exchange successful!")

        # Redirect to frontend
        return redirect('/?auth=success')
    except Exception as e:
        print(f"[ERROR] Token exchange failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    service = get_spotify_service()
    if load_spotify_tokens(service) and service.is_token_valid():
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.pop('spotify_tokens', None)
    return jsonify({'success': True})


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


@app.route('/api/playlists/<playlist_id>/tracks')
def get_playlist_tracks_endpoint(playlist_id: str):
    """Get tracks from a playlist"""
    service = get_spotify_service()
    if not load_spotify_tokens(service):
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        tracks = service.get_all_playlist_tracks(playlist_id)
        return jsonify({'tracks': tracks})
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
        playlists = service.get_all_user_playlists()[:10]  # Limit to 10 playlists

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
                    'duration': track['duration_ms'] / 1000,
                    'spotify_uri': track['uri'],
                    'album_art': track['album']['images'][0]['url'] if track['album'].get('images') else None,
                    'popularity': track.get('popularity', 50),
                })

        # Learn preferences
        preferences = MusicRecommendationEngine.learn_preferences(tracks_with_features)

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
def generate_queue():
    """Generate adaptive music queue"""
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
        queue = MusicRecommendationEngine.generate_queue(
            tracks,
            preferences,
            context,
            keywords,
            queue_size=10
        )

        return jsonify({'queue': queue})
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
