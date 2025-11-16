// Spotify API Configuration
export const SPOTIFY_CONFIG = {
  CLIENT_ID: process.env.REACT_APP_SPOTIFY_CLIENT_ID || 'YOUR_CLIENT_ID_HERE',
  REDIRECT_URI: process.env.REACT_APP_REDIRECT_URI || 'http://localhost:3000/callback',
  SCOPES: [
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
  ].join(' '),
  AUTH_ENDPOINT: 'https://accounts.spotify.com/authorize',
  TOKEN_ENDPOINT: 'https://accounts.spotify.com/api/token',
  API_BASE_URL: 'https://api.spotify.com/v1',
};

// Helper to generate random string for state parameter
export const generateRandomString = (length) => {
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const values = crypto.getRandomValues(new Uint8Array(length));
  return values.reduce((acc, x) => acc + possible[x % possible.length], '');
};

// Generate code verifier for PKCE
export const generateCodeVerifier = () => {
  return generateRandomString(64);
};

// Generate code challenge from verifier
export const generateCodeChallenge = async (codeVerifier) => {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(codeVerifier)
  );
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
};
