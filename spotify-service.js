import { SPOTIFY_CONFIG, generateCodeVerifier, generateCodeChallenge } from './spotify-config';

class SpotifyService {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
  }

  // Initialize OAuth flow
  async login() {
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);

    // Store code verifier in sessionStorage for later use
    sessionStorage.setItem('code_verifier', codeVerifier);

    const params = new URLSearchParams({
      client_id: SPOTIFY_CONFIG.CLIENT_ID,
      response_type: 'code',
      redirect_uri: SPOTIFY_CONFIG.REDIRECT_URI,
      scope: SPOTIFY_CONFIG.SCOPES,
      code_challenge_method: 'S256',
      code_challenge: codeChallenge,
    });

    window.location.href = `${SPOTIFY_CONFIG.AUTH_ENDPOINT}?${params.toString()}`;
  }

  // Handle OAuth callback
  async handleCallback(code) {
    const codeVerifier = sessionStorage.getItem('code_verifier');

    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }

    const params = new URLSearchParams({
      client_id: SPOTIFY_CONFIG.CLIENT_ID,
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: SPOTIFY_CONFIG.REDIRECT_URI,
      code_verifier: codeVerifier,
    });

    const response = await fetch(SPOTIFY_CONFIG.TOKEN_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    if (!response.ok) {
      throw new Error('Failed to exchange code for token');
    }

    const data = await response.json();
    this.setTokens(data);
    sessionStorage.removeItem('code_verifier');

    return data;
  }

  // Set tokens and expiry
  setTokens(data) {
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    this.tokenExpiry = Date.now() + data.expires_in * 1000;

    // Store in localStorage for persistence
    localStorage.setItem('spotify_access_token', this.accessToken);
    localStorage.setItem('spotify_refresh_token', this.refreshToken);
    localStorage.setItem('spotify_token_expiry', this.tokenExpiry.toString());
  }

  // Load tokens from localStorage
  loadTokens() {
    this.accessToken = localStorage.getItem('spotify_access_token');
    this.refreshToken = localStorage.getItem('spotify_refresh_token');
    const expiry = localStorage.getItem('spotify_token_expiry');
    this.tokenExpiry = expiry ? parseInt(expiry) : null;

    return !!this.accessToken;
  }

  // Check if token is valid
  isTokenValid() {
    return this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry;
  }

  // Refresh access token
  async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const params = new URLSearchParams({
      client_id: SPOTIFY_CONFIG.CLIENT_ID,
      grant_type: 'refresh_token',
      refresh_token: this.refreshToken,
    });

    const response = await fetch(SPOTIFY_CONFIG.TOKEN_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();
    this.setTokens({ ...data, refresh_token: this.refreshToken });

    return data;
  }

  // Make authenticated API request
  async apiRequest(endpoint, options = {}) {
    // Check if token needs refresh
    if (!this.isTokenValid() && this.refreshToken) {
      await this.refreshAccessToken();
    }

    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${SPOTIFY_CONFIG.API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Token expired, try to refresh
      if (this.refreshToken) {
        await this.refreshAccessToken();
        return this.apiRequest(endpoint, options);
      }
      throw new Error('Authentication failed');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || 'API request failed');
    }

    return response.json();
  }

  // Get user profile
  async getUserProfile() {
    return this.apiRequest('/me');
  }

  // Get user's playlists
  async getUserPlaylists(limit = 50, offset = 0) {
    return this.apiRequest(`/me/playlists?limit=${limit}&offset=${offset}`);
  }

  // Get all user's playlists (handles pagination)
  async getAllUserPlaylists() {
    const allPlaylists = [];
    let offset = 0;
    const limit = 50;
    let hasMore = true;

    while (hasMore) {
      const response = await this.getUserPlaylists(limit, offset);
      allPlaylists.push(...response.items);

      if (response.next) {
        offset += limit;
      } else {
        hasMore = false;
      }
    }

    return allPlaylists;
  }

  // Get playlist tracks
  async getPlaylistTracks(playlistId, limit = 100, offset = 0) {
    return this.apiRequest(`/playlists/${playlistId}/tracks?limit=${limit}&offset=${offset}`);
  }

  // Get all tracks from a playlist (handles pagination)
  async getAllPlaylistTracks(playlistId) {
    const allTracks = [];
    let offset = 0;
    const limit = 100;
    let hasMore = true;

    while (hasMore) {
      const response = await this.getPlaylistTracks(playlistId, limit, offset);
      allTracks.push(...response.items);

      if (response.next) {
        offset += limit;
      } else {
        hasMore = false;
      }
    }

    return allTracks;
  }

  // Get audio features for multiple tracks
  async getAudioFeatures(trackIds) {
    // Spotify API allows max 100 tracks per request
    const chunks = [];
    for (let i = 0; i < trackIds.length; i += 100) {
      chunks.push(trackIds.slice(i, i + 100));
    }

    const allFeatures = [];
    for (const chunk of chunks) {
      const response = await this.apiRequest(`/audio-features?ids=${chunk.join(',')}`);
      allFeatures.push(...response.audio_features);
    }

    return allFeatures;
  }

  // Get user's top tracks
  async getTopTracks(timeRange = 'medium_term', limit = 50) {
    return this.apiRequest(`/me/top/tracks?time_range=${timeRange}&limit=${limit}`);
  }

  // Get recommendations based on seed tracks
  async getRecommendations(seedTracks, limit = 20, targetFeatures = {}) {
    const params = new URLSearchParams({
      seed_tracks: seedTracks.slice(0, 5).join(','), // Max 5 seed tracks
      limit: limit.toString(),
    });

    // Add target audio features if provided
    Object.entries(targetFeatures).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(`target_${key}`, value.toString());
      }
    });

    return this.apiRequest(`/recommendations?${params.toString()}`);
  }

  // Play tracks
  async play(uris, deviceId = null) {
    const body = { uris };
    const endpoint = deviceId ? `/me/player/play?device_id=${deviceId}` : '/me/player/play';

    return this.apiRequest(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  // Pause playback
  async pause() {
    return this.apiRequest('/me/player/pause', {
      method: 'PUT',
    });
  }

  // Skip to next track
  async skipToNext() {
    return this.apiRequest('/me/player/next', {
      method: 'POST',
    });
  }

  // Get current playback state
  async getCurrentPlayback() {
    return this.apiRequest('/me/player');
  }

  // Get available devices
  async getDevices() {
    return this.apiRequest('/me/player/devices');
  }

  // Search for tracks
  async searchTracks(query, limit = 20) {
    const params = new URLSearchParams({
      q: query,
      type: 'track',
      limit: limit.toString(),
    });
    return this.apiRequest(`/search?${params.toString()}`);
  }

  // Logout
  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    localStorage.removeItem('spotify_access_token');
    localStorage.removeItem('spotify_refresh_token');
    localStorage.removeItem('spotify_token_expiry');
  }
}

export default new SpotifyService();
