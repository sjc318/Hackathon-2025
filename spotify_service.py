"""
Spotify API Service for Python
Handles authentication and API requests to Spotify Web API
"""

import requests
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class SpotifyService:
    """Service class for Spotify Web API integration"""

    AUTH_ENDPOINT = "https://accounts.spotify.com/authorize"
    TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"

    SCOPES = [
        'user-read-private',
        'user-read-email',
        'playlist-read-private',
        'playlist-read-collaborative',
        'user-library-read',
        'user-read-playback-state',
        'user-modify-playback-state',
        'user-read-currently-playing',
        'streaming',
        'user-top-read',
    ]

    def __init__(self, client_id: str, redirect_uri: str):
        """
        Initialize Spotify service

        Args:
            client_id: Spotify application client ID
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    @staticmethod
    def generate_code_verifier(length: int = 64) -> str:
        """Generate a random code verifier for PKCE"""
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def generate_code_challenge(verifier: str) -> str:
        """Generate code challenge from verifier for PKCE"""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

    def get_authorization_url(self, code_challenge: str, state: str) -> str:
        """
        Get Spotify authorization URL for OAuth flow

        Args:
            code_challenge: PKCE code challenge
            state: Random state for CSRF protection

        Returns:
            Authorization URL
        """
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.SCOPES),
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge,
            'state': state,
        }

        query_string = '&'.join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        return f"{self.AUTH_ENDPOINT}?{query_string}"

    def exchange_code_for_token(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            code_verifier: PKCE code verifier

        Returns:
            Token response data
        """
        data = {
            'client_id': self.client_id,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier,
        }

        response = requests.post(self.TOKEN_ENDPOINT, data=data)
        response.raise_for_status()

        token_data = response.json()
        self._set_tokens(token_data)
        return token_data

    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using refresh token

        Returns:
            New token data
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        data = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }

        response = requests.post(self.TOKEN_ENDPOINT, data=data)
        response.raise_for_status()

        token_data = response.json()
        # Preserve refresh token if not returned
        if 'refresh_token' not in token_data:
            token_data['refresh_token'] = self.refresh_token
        self._set_tokens(token_data)
        return token_data

    def _set_tokens(self, token_data: Dict[str, Any]) -> None:
        """Set access and refresh tokens from token response"""
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token', self.refresh_token)
        self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])

    def is_token_valid(self) -> bool:
        """Check if current access token is valid"""
        return (
            self.access_token is not None
            and self.token_expiry is not None
            and datetime.now() < self.token_expiry
        )

    def _api_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Any:
        """
        Make authenticated API request to Spotify

        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            JSON response data
        """
        # Refresh token if needed
        if not self.is_token_valid() and self.refresh_token:
            self.refresh_access_token()

        if not self.access_token:
            raise ValueError("Not authenticated")

        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"

        url = f"{self.API_BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401 and self.refresh_token:
            # Token expired, try to refresh
            self.refresh_access_token()
            headers['Authorization'] = f"Bearer {self.access_token}"
            response = requests.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()

        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return None

        return response.json()

    # User Profile Methods
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user's profile"""
        return self._api_request('/me')

    def get_user_top_tracks(self, limit: int = 50, time_range: str = 'medium_term') -> Dict[str, Any]:
        """
        Get user's top tracks

        Args:
            limit: Number of tracks to retrieve (max 50)
            time_range: Time range for top tracks
                - short_term: last 4 weeks
                - medium_term: last 6 months (default)
                - long_term: all time

        Returns:
            Dict containing top tracks data with audio features
        """
        limit = min(limit, 50)  # Spotify API max
        endpoint = f'/me/top/tracks?limit={limit}&time_range={time_range}'
        return self._api_request(endpoint)

    # Playlist Methods
    def get_user_playlists(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get user's playlists with pagination"""
        return self._api_request(f'/me/playlists?limit={limit}&offset={offset}')

    def get_all_user_playlists(self) -> List[Dict[str, Any]]:
        """Get all user's playlists (handles pagination)"""
        all_playlists = []
        offset = 0
        limit = 50

        while True:
            response = self.get_user_playlists(limit=limit, offset=offset)
            all_playlists.extend(response['items'])

            if response['next'] is None:
                break
            offset += limit

        return all_playlists

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get tracks from a playlist"""
        return self._api_request(f'/playlists/{playlist_id}/tracks?limit={limit}&offset={offset}')

    def get_all_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all tracks from a playlist (handles pagination)"""
        all_tracks = []
        offset = 0
        limit = 100

        while True:
            response = self.get_playlist_tracks(playlist_id, limit=limit, offset=offset)
            all_tracks.extend(response['items'])

            if response['next'] is None:
                break
            offset += limit

        return all_tracks

    # Audio Features Methods
    def get_audio_features(self, track_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """
        Get audio features for multiple tracks

        Args:
            track_ids: List of track IDs (max 100)

        Returns:
            List of audio features
        """
        all_features = []

        # Spotify API allows max 100 tracks per request
        for i in range(0, len(track_ids), 100):
            chunk = track_ids[i:i + 100]
            ids_string = ','.join(chunk)
            response = self._api_request(f'/audio-features?ids={ids_string}')
            all_features.extend(response['audio_features'])

        return all_features

    def get_track_audio_features(self, track_id: str) -> Dict[str, Any]:
        """Get audio features for a single track"""
        return self._api_request(f'/audio-features/{track_id}')

    # Top Tracks Methods
    def get_top_tracks(self, time_range: str = 'medium_term', limit: int = 50) -> Dict[str, Any]:
        """
        Get user's top tracks

        Args:
            time_range: 'short_term', 'medium_term', or 'long_term'
            limit: Number of tracks to return (max 50)
        """
        return self._api_request(f'/me/top/tracks?time_range={time_range}&limit={limit}')

    # Recommendations Methods
    def get_recommendations(
        self,
        seed_tracks: List[str],
        limit: int = 20,
        target_features: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get track recommendations

        Args:
            seed_tracks: List of track IDs to base recommendations on (max 5)
            limit: Number of recommendations
            target_features: Dict of target audio features (e.g., {'energy': 0.8, 'valence': 0.6})
        """
        # Limit to 5 seed tracks
        seed_tracks = seed_tracks[:5]

        params = {
            'seed_tracks': ','.join(seed_tracks),
            'limit': limit,
        }

        # Add target features if provided
        if target_features:
            for key, value in target_features.items():
                params[f'target_{key}'] = value

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return self._api_request(f'/recommendations?{query_string}')

    # Playback Control Methods
    def play(self, uris: Optional[List[str]] = None, device_id: Optional[str] = None) -> None:
        """
        Start or resume playback

        Args:
            uris: List of Spotify URIs to play
            device_id: Device ID to play on
        """
        endpoint = '/me/player/play'
        if device_id:
            endpoint += f'?device_id={device_id}'

        body = {}
        if uris:
            body['uris'] = uris

        self._api_request(endpoint, method='PUT', json=body)

    def pause(self) -> None:
        """Pause playback"""
        self._api_request('/me/player/pause', method='PUT')

    def skip_to_next(self) -> None:
        """Skip to next track"""
        self._api_request('/me/player/next', method='POST')

    def skip_to_previous(self) -> None:
        """Skip to previous track"""
        self._api_request('/me/player/previous', method='POST')

    def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get current playback state"""
        return self._api_request('/me/player')

    def get_devices(self) -> Dict[str, Any]:
        """Get available devices"""
        return self._api_request('/me/player/devices')

    # Search Methods
    def search_tracks(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for tracks"""
        encoded_query = requests.utils.quote(query)
        return self._api_request(f'/search?q={encoded_query}&type=track&limit={limit}')

    def set_token_data(self, access_token: str, refresh_token: str, expires_in: int) -> None:
        """
        Manually set token data (useful for loading from session)

        Args:
            access_token: Access token
            refresh_token: Refresh token
            expires_in: Seconds until token expires
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

    def get_token_data(self) -> Optional[Dict[str, Any]]:
        """Get current token data for storage"""
        if not self.access_token:
            return None

        expires_in = 0
        if self.token_expiry:
            expires_in = int((self.token_expiry - datetime.now()).total_seconds())

        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': max(0, expires_in),
        }
