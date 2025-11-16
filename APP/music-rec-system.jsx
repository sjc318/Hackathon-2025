import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, Music, RefreshCw, TrendingUp, LogOut } from 'lucide-react';
import spotifyService from '../spotify-service';

export default function AdaptiveMusicSystem() {
  const [userPreferences, setUserPreferences] = useState(null);
  const [context, setContext] = useState({
    weather: 'sunny',
    location: 'home',
    activity: 'relaxing',
    timeOfDay: 'afternoon',
    temperature: 72
  });
  const [keywords, setKeywords] = useState('');
  const [queue, setQueue] = useState([]);
  const [currentSong, setCurrentSong] = useState(null);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [listeningHistory, setListeningHistory] = useState([]);
  const [adaptationLog, setAdaptationLog] = useState([]);
  const [showSetup, setShowSetup] = useState(true);
  const [spotifyConnected, setSpotifyConnected] = useState(false);
  const [mcpEnabled, setMcpEnabled] = useState(false);
  const [skipThreshold, setSkipThreshold] = useState(0.3);
  const [userBehaviorProfile, setUserBehaviorProfile] = useState({
    totalSkips: 0,
    earlySkips: 0,
    lateSkips: 0,
    avgCompletionRate: 0,
    skipPatience: 'medium'
  });
  const [spotifyPlaylists, setSpotifyPlaylists] = useState([]);
  const [spotifyTracks, setSpotifyTracks] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const playbackInterval = useRef(null);

  // Check for OAuth callback on mount
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');

      if (code) {
        try {
          addAdaptationLog('Completing Spotify authentication...');
          await spotifyService.handleCallback(code);
          setSpotifyConnected(true);
          addAdaptationLog('✓ Successfully authenticated with Spotify');

          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);

          // Load user profile
          await loadUserProfile();
        } catch (error) {
          console.error('OAuth callback error:', error);
          addAdaptationLog(`Authentication failed: ${error.message}`);
          setError(error.message);
        }
      } else {
        // Check if we have existing tokens
        const hasTokens = spotifyService.loadTokens();
        if (hasTokens && spotifyService.isTokenValid()) {
          setSpotifyConnected(true);
          loadUserProfile();
        }
      }
    };

    handleOAuthCallback();
  }, []);

  const loadUserProfile = async () => {
    try {
      const profile = await spotifyService.getUserProfile();
      setUserProfile(profile);
      addAdaptationLog(`Welcome, ${profile.display_name}!`);
    } catch (error) {
      console.error('Failed to load user profile:', error);
    }
  };

  const fetchMCPContext = async () => {
    addAdaptationLog('Fetching context from MCP servers...');

    try {
      const locationData = await simulateMCPCall('location');
      const weatherData = await simulateMCPCall('weather');
      const timeData = await simulateMCPCall('time');

      setContext(prev => ({
        ...prev,
        location: locationData.location,
        weather: weatherData.condition,
        temperature: weatherData.temperature,
        timeOfDay: timeData.period
      }));

      setMcpEnabled(true);
      addAdaptationLog(`Context updated: ${weatherData.condition} weather at ${locationData.location}, ${timeData.period}`);
    } catch (error) {
      addAdaptationLog('MCP context fetch failed, using manual settings');
      setMcpEnabled(false);
    }
  };

  const simulateMCPCall = async (type) => {
    await new Promise(resolve => setTimeout(resolve, 500));

    if (type === 'location') {
      const locations = ['home', 'gym', 'office', 'commute'];
      return { location: locations[Math.floor(Math.random() * locations.length)] };
    } else if (type === 'weather') {
      const conditions = ['sunny', 'rainy', 'cloudy', 'clear'];
      return {
        condition: conditions[Math.floor(Math.random() * conditions.length)],
        temperature: Math.floor(Math.random() * 40) + 50
      };
    } else if (type === 'time') {
      const hour = new Date().getHours();
      let period = 'afternoon';
      if (hour < 6) period = 'night';
      else if (hour < 12) period = 'morning';
      else if (hour < 17) period = 'afternoon';
      else if (hour < 21) period = 'evening';
      else period = 'night';
      return { period };
    }
  };

  const connectSpotify = async () => {
    try {
      addAdaptationLog('Redirecting to Spotify login...');
      await spotifyService.login();
    } catch (error) {
      console.error('Spotify connection error:', error);
      addAdaptationLog(`Failed to connect: ${error.message}`);
      setError(error.message);
    }
  };

  const fetchSpotifyPlaylists = async () => {
    if (!spotifyConnected) {
      addAdaptationLog('Please connect to Spotify first');
      return;
    }

    setLoading(true);
    addAdaptationLog('Fetching your Spotify playlists...');

    try {
      const playlists = await spotifyService.getAllUserPlaylists();
      setSpotifyPlaylists(playlists);
      addAdaptationLog(`✓ Loaded ${playlists.length} playlists`);

      // Automatically fetch tracks from all playlists
      await fetchAllPlaylistTracks(playlists);
    } catch (error) {
      console.error('Failed to fetch playlists:', error);
      addAdaptationLog(`Failed to fetch playlists: ${error.message}`);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllPlaylistTracks = async (playlists) => {
    addAdaptationLog('Loading tracks from your playlists...');
    const allTracks = [];

    try {
      // Fetch tracks from first 10 playlists to avoid rate limits
      const playlistsToFetch = playlists.slice(0, 10);

      for (const playlist of playlistsToFetch) {
        const tracks = await spotifyService.getAllPlaylistTracks(playlist.id);
        allTracks.push(...tracks.filter(item => item.track && item.track.id));
      }

      // Get unique tracks
      const uniqueTracks = Array.from(
        new Map(allTracks.map(item => [item.track.id, item.track])).values()
      );

      addAdaptationLog(`✓ Loaded ${uniqueTracks.length} unique tracks`);

      // Fetch audio features for all tracks
      await fetchAudioFeatures(uniqueTracks);
    } catch (error) {
      console.error('Failed to fetch playlist tracks:', error);
      addAdaptationLog(`Error loading tracks: ${error.message}`);
    }
  };

  const fetchAudioFeatures = async (tracks) => {
    addAdaptationLog('Analyzing audio features...');

    try {
      const trackIds = tracks.map(track => track.id);
      const audioFeatures = await spotifyService.getAudioFeatures(trackIds);

      // Combine track data with audio features
      const tracksWithFeatures = tracks.map((track, index) => {
        const features = audioFeatures[index];
        return {
          id: track.id,
          title: track.name,
          artist: track.artists.map(a => a.name).join(', '),
          genre: track.album?.genres?.[0] || 'Unknown',
          tempo: features?.tempo || 120,
          energy: features?.energy || 0.5,
          valence: features?.valence || 0.5,
          acousticness: features?.acousticness || 0.5,
          duration: track.duration_ms / 1000,
          spotifyUri: track.uri,
          albumArt: track.album?.images?.[0]?.url,
          popularity: track.popularity || 50,
        };
      });

      setSpotifyTracks(tracksWithFeatures);
      addAdaptationLog(`✓ Analyzed ${tracksWithFeatures.length} tracks`);

      // Learn preferences from the tracks
      const preferences = learnPreferences(tracksWithFeatures);
      setUserPreferences(preferences);
    } catch (error) {
      console.error('Failed to fetch audio features:', error);
      addAdaptationLog(`Error analyzing tracks: ${error.message}`);
    }
  };

  const learnPreferences = (tracks) => {
    if (!tracks || tracks.length === 0) return null;

    const avgTempo = tracks.reduce((sum, s) => sum + s.tempo, 0) / tracks.length;
    const avgEnergy = tracks.reduce((sum, s) => sum + s.energy, 0) / tracks.length;
    const avgValence = tracks.reduce((sum, s) => sum + s.valence, 0) / tracks.length;
    const avgAcousticness = tracks.reduce((sum, s) => sum + s.acousticness, 0) / tracks.length;

    const genreCount = {};
    tracks.forEach(s => {
      genreCount[s.genre] = (genreCount[s.genre] || 0) + 1;
    });

    return { avgTempo, avgEnergy, avgValence, avgAcousticness, genrePreferences: genreCount, totalSongs: tracks.length };
  };

  const updateSkipThreshold = () => {
    const history = listeningHistory;
    if (history.length < 5) return;

    const recentHistory = history.slice(-10);
    const avgCompletion = recentHistory.reduce((sum, h) => sum + h.completionRate, 0) / recentHistory.length;
    const earlySkipRate = recentHistory.filter(h => h.completionRate < 0.3).length / recentHistory.length;

    let newThreshold = 0.3;
    let patience = 'medium';

    if (avgCompletion > 0.7) {
      newThreshold = 0.2;
      patience = 'high';
    } else if (avgCompletion < 0.4) {
      newThreshold = 0.5;
      patience = 'low';
    } else if (earlySkipRate > 0.5) {
      newThreshold = 0.4;
      patience = 'low';
    }

    setSkipThreshold(newThreshold);
    setUserBehaviorProfile(prev => ({
      ...prev,
      avgCompletionRate: avgCompletion,
      skipPatience: patience,
      totalSkips: history.filter(h => h.action === 'skipped').length,
      earlySkips: history.filter(h => h.action === 'skipped' && h.completionRate < 0.3).length,
      lateSkips: history.filter(h => h.action === 'skipped' && h.completionRate >= 0.3).length
    }));

    addAdaptationLog(`Skip threshold adjusted to ${(newThreshold * 100).toFixed(0)}% (patience: ${patience})`);
  };

  const generateQueue = () => {
    if (!userPreferences) return;

    const songDatabase = spotifyTracks.length > 0 ? spotifyTracks : [];

    if (songDatabase.length === 0) {
      addAdaptationLog('No tracks available. Please load your Spotify playlists first.');
      return;
    }

    const keywordList = keywords.toLowerCase().split(',').map(k => k.trim());
    const contextModifiers = getContextModifiers(context);

    const scoredSongs = songDatabase.map(song => {
      let score = 0;
      score += (1 - Math.abs(song.tempo - userPreferences.avgTempo) / 150) * 0.1;
      score += (1 - Math.abs(song.energy - userPreferences.avgEnergy)) * 0.1;
      score += (1 - Math.abs(song.valence - userPreferences.avgValence)) * 0.1;
      score += (1 - Math.abs(song.acousticness - userPreferences.avgAcousticness)) * 0.1;

      const genreScore = (userPreferences.genrePreferences[song.genre] || 0) / userPreferences.totalSongs;
      score += genreScore * 0.2;

      if (keywordList.some(kw => kw && (
        song.genre.toLowerCase().includes(kw) ||
        song.title.toLowerCase().includes(kw) ||
        song.artist.toLowerCase().includes(kw)
      ))) {
        score += 0.2;
      }

      score += calculateContextScore(song, contextModifiers) * 0.2;
      return { ...song, score };
    });

    const topSongs = scoredSongs
      .sort((a, b) => b.score - a.score)
      .slice(0, 15)
      .sort(() => Math.random() - 0.5)
      .slice(0, 10);

    setQueue(topSongs);
    setCurrentSong(topSongs[0]);
    setShowSetup(false);
    addAdaptationLog('Initial queue generated based on preferences and context');
  };

  const getContextModifiers = (ctx) => {
    const modifiers = { energyBoost: 0, valenceBoost: 0, tempoBoost: 0, acousticBoost: 0 };

    if (ctx.weather === 'rainy') {
      modifiers.acousticBoost = 0.3;
      modifiers.valenceBoost = -0.2;
      modifiers.energyBoost = -0.2;
    } else if (ctx.weather === 'sunny') {
      modifiers.valenceBoost = 0.3;
      modifiers.energyBoost = 0.2;
    }

    if (ctx.activity === 'working out') {
      modifiers.energyBoost = 0.5;
      modifiers.tempoBoost = 0.4;
    } else if (ctx.activity === 'relaxing') {
      modifiers.energyBoost = -0.3;
      modifiers.acousticBoost = 0.4;
    } else if (ctx.activity === 'focusing') {
      modifiers.acousticBoost = 0.2;
      modifiers.energyBoost = -0.1;
    }

    if (ctx.timeOfDay === 'morning') {
      modifiers.energyBoost += 0.2;
      modifiers.valenceBoost += 0.2;
    } else if (ctx.timeOfDay === 'night') {
      modifiers.energyBoost -= 0.2;
      modifiers.acousticBoost += 0.2;
    }

    return modifiers;
  };

  const calculateContextScore = (song, modifiers) => {
    let score = 0;
    if (modifiers.energyBoost > 0 && song.energy > 0.7) score += 0.3;
    if (modifiers.energyBoost < 0 && song.energy < 0.4) score += 0.3;
    if (modifiers.valenceBoost > 0 && song.valence > 0.7) score += 0.2;
    if (modifiers.valenceBoost < 0 && song.valence < 0.5) score += 0.2;
    if (modifiers.tempoBoost > 0 && song.tempo > 120) score += 0.3;
    if (modifiers.acousticBoost > 0 && song.acousticness > 0.6) score += 0.3;
    return Math.min(score, 1);
  };

  useEffect(() => {
    if (isPlaying) {
      playbackInterval.current = setInterval(() => {
        setPlaybackTime(prev => {
          const newTime = prev + 0.1;
          if (currentSong && newTime >= currentSong.duration) {
            handleSongComplete();
            return 0;
          }
          return newTime;
        });
      }, 100);
    } else {
      if (playbackInterval.current) clearInterval(playbackInterval.current);
    }

    return () => {
      if (playbackInterval.current) clearInterval(playbackInterval.current);
    };
  }, [isPlaying, currentSong]);

  const handleSongComplete = () => {
    if (!currentSong) return;
    const completionRate = playbackTime / currentSong.duration;
    recordListeningBehavior(currentSong, playbackTime, completionRate, 'completed');
    updateSkipThreshold();

    const nextIndex = queue.findIndex(s => s.id === currentSong.id) + 1;
    if (nextIndex < queue.length) {
      setCurrentSong(queue[nextIndex]);
      setPlaybackTime(0);
    } else {
      setIsPlaying(false);
      addAdaptationLog('Queue completed');
    }
  };

  const handleSkip = async () => {
    if (!currentSong) return;
    const completionRate = playbackTime / currentSong.duration;
    recordListeningBehavior(currentSong, playbackTime, completionRate, 'skipped');
    adaptQueue('skip', currentSong, completionRate);
    updateSkipThreshold();

    // Skip on Spotify if connected and playing
    if (spotifyConnected && isPlaying) {
      try {
        await spotifyService.skipToNext();
      } catch (error) {
        console.error('Failed to skip on Spotify:', error);
      }
    }

    const nextIndex = queue.findIndex(s => s.id === currentSong.id) + 1;
    if (nextIndex < queue.length) {
      setCurrentSong(queue[nextIndex]);
      setPlaybackTime(0);
    } else {
      setIsPlaying(false);
    }
  };

  const recordListeningBehavior = (song, listenTime, completionRate, action) => {
    const behavior = {
      songId: song.id,
      title: song.title,
      genre: song.genre,
      listenTime,
      completionRate,
      action,
      timestamp: new Date().toISOString(),
      context: { ...context }
    };
    setListeningHistory(prev => [...prev, behavior]);
  };

  const adaptQueue = (action, song, completionRate) => {
    let adaptation = '';

    if (action === 'skip' && completionRate < skipThreshold) {
      adaptation = `Early skip at ${(completionRate * 100).toFixed(0)}% (threshold: ${(skipThreshold * 100).toFixed(0)}%). Adjusting queue...`;

      const newQueue = queue.filter(s => {
        if (s.id === song.id) return false;
        return calculateSimilarity(s, song) < 0.8;
      });

      const songDatabase = spotifyTracks.length > 0 ? spotifyTracks : [];
      const availableSongs = songDatabase.filter(s =>
        !newQueue.find(q => q.id === s.id) && calculateSimilarity(s, song) < 0.5
      );

      if (availableSongs.length > 0 && newQueue.length < 8) {
        const replacement = availableSongs[Math.floor(Math.random() * availableSongs.length)];
        newQueue.push(replacement);
        adaptation += ` Added "${replacement.title}".`;
      }
      setQueue(newQueue);
    } else if (completionRate > 0.85) {
      adaptation = `High engagement (${(completionRate * 100).toFixed(0)}%). Adding similar tracks.`;
      const songDatabase = spotifyTracks.length > 0 ? spotifyTracks : [];
      const similarSongs = songDatabase.filter(s =>
        !queue.find(q => q.id === s.id) && s.id !== song.id && calculateSimilarity(s, song) > 0.6
      );

      if (similarSongs.length > 0) {
        const newSong = similarSongs[Math.floor(Math.random() * similarSongs.length)];
        setQueue(prev => [...prev, newSong]);
        adaptation += ` Queued "${newSong.title}".`;
      }
    }

    if (adaptation) addAdaptationLog(adaptation);
  };

  const calculateSimilarity = (song1, song2) => {
    let similarity = 0;
    if (song1.genre === song2.genre) similarity += 0.3;
    similarity += (1 - Math.abs(song1.energy - song2.energy)) * 0.2;
    similarity += (1 - Math.abs(song1.valence - song2.valence)) * 0.2;
    similarity += (1 - Math.abs(song1.tempo - song2.tempo) / 150) * 0.15;
    similarity += (1 - Math.abs(song1.acousticness - song2.acousticness)) * 0.15;
    return similarity;
  };

  const addAdaptationLog = (message) => {
    setAdaptationLog(prev => [...prev, { message, timestamp: new Date().toLocaleTimeString() }]);
  };

  const togglePlayback = async () => {
    if (spotifyConnected && currentSong) {
      try {
        if (isPlaying) {
          await spotifyService.pause();
        } else {
          // Play current queue on Spotify
          const uris = queue.map(song => song.spotifyUri);
          await spotifyService.play(uris);
        }
      } catch (error) {
        console.error('Playback control error:', error);
        addAdaptationLog('Note: For full playback control, Spotify Premium is required');
      }
    }
    setIsPlaying(!isPlaying);
  };

  const handleLogout = () => {
    spotifyService.logout();
    setSpotifyConnected(false);
    setUserProfile(null);
    setSpotifyPlaylists([]);
    setSpotifyTracks([]);
    setUserPreferences(null);
    setQueue([]);
    setCurrentSong(null);
    setShowSetup(true);
    addAdaptationLog('Logged out from Spotify');
  };

  const progressPercentage = currentSong ? (playbackTime / currentSong.duration) * 100 : 0;

  if (showSetup) {
    return (
      <div className="w-full h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white p-6 overflow-auto">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold mb-2">Adaptive Music System</h1>
              <p className="text-blue-200">AI-powered music that adapts to you</p>
            </div>
            {spotifyConnected && userProfile && (
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 px-4 py-2 rounded-lg transition-all"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            )}
          </div>

          {error && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 mb-6">
              <p className="text-red-200">{error}</p>
            </div>
          )}

          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Music className="w-6 h-6 text-green-400" />
              Spotify Integration
            </h2>
            {userProfile && (
              <div className="mb-4 p-3 bg-green-500/20 rounded-lg">
                <p className="text-green-200">Logged in as: <strong>{userProfile.display_name}</strong></p>
                {userProfile.email && <p className="text-sm text-green-300">{userProfile.email}</p>}
              </div>
            )}
            <div className="flex gap-4">
              <button
                onClick={connectSpotify}
                disabled={spotifyConnected || loading}
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  spotifyConnected ? 'bg-green-500/30 text-green-200 cursor-not-allowed' : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {spotifyConnected ? '✓ Connected to Spotify' : 'Connect Spotify'}
              </button>
              <button
                onClick={fetchSpotifyPlaylists}
                disabled={!spotifyConnected || loading}
                className="flex-1 bg-white/20 hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed py-3 rounded-lg font-semibold transition-all"
              >
                {loading ? 'Loading...' : 'Load My Playlists'}
              </button>
            </div>
            <p className="text-sm text-blue-200 mt-3">
              {spotifyConnected
                ? `Connected! ${spotifyTracks.length > 0 ? `Loaded ${spotifyTracks.length} tracks.` : 'Click "Load My Playlists" to analyze your music.'}`
                : 'Connect to access your playlists and get personalized recommendations.'}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <RefreshCw className="w-6 h-6 text-blue-400" />
              MCP Context Integration
            </h2>
            <button
              onClick={fetchMCPContext}
              className={`w-full py-3 rounded-lg font-semibold transition-all ${
                mcpEnabled ? 'bg-blue-500/30 text-blue-200' : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              {mcpEnabled ? '✓ Context Auto-Updated' : 'Enable Auto Context (MCP)'}
            </button>
            <p className="text-sm text-blue-200 mt-3">
              MCP servers auto-detect location, weather, and time for optimized music selection.
            </p>
          </div>

          {userPreferences && (
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">Your Music Profile</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-sm text-blue-200">Average Tempo</div>
                  <div className="text-2xl font-bold">{userPreferences.avgTempo.toFixed(0)} BPM</div>
                </div>
                <div>
                  <div className="text-sm text-blue-200">Energy Level</div>
                  <div className="text-2xl font-bold">{(userPreferences.avgEnergy * 100).toFixed(0)}%</div>
                </div>
                <div>
                  <div className="text-sm text-blue-200">Positivity</div>
                  <div className="text-2xl font-bold">{(userPreferences.avgValence * 100).toFixed(0)}%</div>
                </div>
                <div>
                  <div className="text-sm text-blue-200">Acoustic Preference</div>
                  <div className="text-2xl font-bold">{(userPreferences.avgAcousticness * 100).toFixed(0)}%</div>
                </div>
              </div>
              <div>
                <div className="text-sm text-blue-200 mb-2">Music Analysis</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(userPreferences.genrePreferences).slice(0, 6).map(([genre, count]) => (
                    <span key={genre} className="bg-blue-500/30 px-3 py-1 rounded-full text-sm">
                      {genre} ({count})
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Current Context</h2>
            {!mcpEnabled && (
              <p className="text-sm text-yellow-300 mb-4">⚠️ Manual mode - Enable MCP for automatic updates</p>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-blue-200 mb-2">Weather</label>
                <select
                  value={context.weather}
                  onChange={(e) => setContext({...context, weather: e.target.value})}
                  disabled={mcpEnabled}
                  className="w-full bg-white/20 rounded px-3 py-2 text-white disabled:opacity-50"
                >
                  <option value="sunny">☀️ Sunny</option>
                  <option value="rainy">🌧️ Rainy</option>
                  <option value="cloudy">☁️ Cloudy</option>
                  <option value="clear">🌙 Clear Night</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-blue-200 mb-2">Location</label>
                <select
                  value={context.location}
                  onChange={(e) => setContext({...context, location: e.target.value})}
                  disabled={mcpEnabled}
                  className="w-full bg-white/20 rounded px-3 py-2 text-white disabled:opacity-50"
                >
                  <option value="home">🏠 Home</option>
                  <option value="gym">💪 Gym</option>
                  <option value="commute">🚗 Commute</option>
                  <option value="office">💼 Office</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-blue-200 mb-2">Activity</label>
                <select
                  value={context.activity}
                  onChange={(e) => setContext({...context, activity: e.target.value})}
                  className="w-full bg-white/20 rounded px-3 py-2 text-white"
                >
                  <option value="relaxing">😌 Relaxing</option>
                  <option value="working out">🏃 Working Out</option>
                  <option value="focusing">🎯 Focusing</option>
                  <option value="partying">🎉 Partying</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-blue-200 mb-2">Time of Day</label>
                <select
                  value={context.timeOfDay}
                  onChange={(e) => setContext({...context, timeOfDay: e.target.value})}
                  disabled={mcpEnabled}
                  className="w-full bg-white/20 rounded px-3 py-2 text-white disabled:opacity-50"
                >
                  <option value="morning">🌅 Morning</option>
                  <option value="afternoon">☀️ Afternoon</option>
                  <option value="evening">🌆 Evening</option>
                  <option value="night">🌙 Night</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">Keywords (Optional)</h2>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g., energetic, chill, electronic, rock"
              className="w-full bg-white/20 rounded px-4 py-3 text-white placeholder-blue-200"
            />
            <p className="text-sm text-blue-200 mt-2">Separate multiple keywords with commas</p>
          </div>

          <button
            onClick={generateQueue}
            disabled={!userPreferences || spotifyTracks.length === 0}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-lg text-xl transition-all"
          >
            {spotifyTracks.length === 0 ? 'Load Playlists First' : 'Generate My Playlist 🎵'}
          </button>

          {/* Adaptation Log Preview */}
          {adaptationLog.length > 0 && (
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 mt-6">
              <h3 className="text-lg font-bold mb-3">Recent Activity</h3>
              <div className="space-y-2 max-h-48 overflow-auto">
                {adaptationLog.slice().reverse().slice(0, 5).map((log, idx) => (
                  <div key={idx} className="bg-white/10 p-2 rounded text-sm">
                    <span className="text-blue-300 text-xs">{log.timestamp}</span> - {log.message}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex flex-col">
      <div className="bg-black/20 backdrop-blur-md p-4 border-b border-white/10">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Adaptive Music System</h1>
          <div className="flex gap-4 text-sm items-center">
            <div className="flex items-center gap-2">
              <span>{context.weather === 'sunny' ? '☀️' : context.weather === 'rainy' ? '🌧️' : context.weather === 'cloudy' ? '☁️' : '🌙'}</span>
              <span>{context.weather}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>📍</span>
              <span>{context.location}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>🎯</span>
              <span>{context.activity}</span>
            </div>
            <div className="flex items-center gap-2">
              <span>🕐</span>
              <span>{context.timeOfDay}</span>
            </div>
            <button
              onClick={handleLogout}
              className="ml-4 flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 px-3 py-1 rounded transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex">
        <div className="flex-1 flex flex-col p-6">
          {currentSong && (
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-8 mb-6">
              {currentSong.albumArt && (
                <img
                  src={currentSong.albumArt}
                  alt="Album art"
                  className="w-32 h-32 rounded-lg mb-4 mx-auto shadow-lg"
                />
              )}
              <div className="text-sm text-blue-200 mb-2">Now Playing</div>
              <h2 className="text-4xl font-bold mb-2">{currentSong.title}</h2>
              <p className="text-xl text-blue-200 mb-6">{currentSong.artist}</p>

              <div className="flex gap-4 mb-6 text-sm flex-wrap">
                <span className="bg-blue-500/30 px-3 py-1 rounded-full">{currentSong.genre}</span>
                <span className="bg-purple-500/30 px-3 py-1 rounded-full">{currentSong.tempo.toFixed(0)} BPM</span>
                <span className="bg-pink-500/30 px-3 py-1 rounded-full">Energy: {(currentSong.energy * 100).toFixed(0)}%</span>
                {spotifyConnected && (
                  <span className="bg-green-500/30 px-3 py-1 rounded-full">🎵 Spotify</span>
                )}
              </div>

              <div className="mb-4">
                <div className="w-full bg-white/20 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-400 to-purple-400 h-full transition-all"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm text-blue-200 mt-2">
                  <span>{Math.floor(playbackTime / 60)}:{(playbackTime % 60).toFixed(0).padStart(2, '0')}</span>
                  <span>{Math.floor(currentSong.duration / 60)}:{(currentSong.duration % 60).toFixed(0).padStart(2, '0')}</span>
                </div>
              </div>

              <div className="flex justify-center gap-4">
                <button
                  onClick={togglePlayback}
                  className="bg-white/20 hover:bg-white/30 p-4 rounded-full transition-all"
                >
                  {isPlaying ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8" />}
                </button>
                <button
                  onClick={handleSkip}
                  className="bg-white/20 hover:bg-white/30 p-4 rounded-full transition-all"
                >
                  <SkipForward className="w-8 h-8" />
                </button>
              </div>
            </div>
          )}

          <div className="bg-white/10 backdrop-blur-md rounded-lg p-6 flex-1 overflow-auto">
            <h3 className="text-xl font-bold mb-4">Up Next ({queue.length} songs)</h3>
            <div className="space-y-2">
              {queue.map((song) => (
                <div
                  key={song.id}
                  className={`p-3 rounded-lg transition-all ${
                    currentSong?.id === song.id ? 'bg-blue-500/30 border-2 border-blue-400' : 'bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="flex justify-between items-center gap-3">
                    {song.albumArt && (
                      <img src={song.albumArt} alt="" className="w-12 h-12 rounded" />
                    )}
                    <div className="flex-1">
                      <div className="font-semibold">{song.title}</div>
                      <div className="text-sm text-blue-200">{song.artist} • {song.genre}</div>
                    </div>
                    <div className="text-sm text-blue-200">
                      {Math.floor(song.duration / 60)}:{(song.duration % 60).toFixed(0).padStart(2, '0')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="w-96 bg-black/30 backdrop-blur-md p-6 overflow-auto">
          <h3 className="text-xl font-bold mb-4">System Analytics</h3>

          <div className="bg-white/10 rounded-lg p-4 mb-6">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              Adaptive Behavior Profile
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-200">Skip Threshold</span>
                <span className="font-semibold">{(skipThreshold * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Skip Patience</span>
                <span className={`font-semibold ${
                  userBehaviorProfile.skipPatience === 'high' ? 'text-green-400' :
                  userBehaviorProfile.skipPatience === 'low' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {userBehaviorProfile.skipPatience}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Avg Completion</span>
                <span className="font-semibold">{(userBehaviorProfile.avgCompletionRate * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Total Skips</span>
                <span className="font-semibold">{userBehaviorProfile.totalSkips}</span>
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="font-semibold mb-2 text-blue-200">Adaptation Log</h4>
            <div className="space-y-2 max-h-64 overflow-auto">
              {adaptationLog.slice().reverse().map((log, idx) => (
                <div key={idx} className="bg-white/10 p-3 rounded text-sm">
                  <div className="text-blue-300 text-xs mb-1">{log.timestamp}</div>
                  <div>{log.message}</div>
                </div>
              ))}
              {adaptationLog.length === 0 && (
                <div className="text-blue-200 text-sm">No adaptations yet. Start listening!</div>
              )}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-2 text-blue-200">Listening History</h4>
            <div className="space-y-2 max-h-96 overflow-auto">
              {listeningHistory.slice().reverse().map((entry, idx) => (
                <div key={idx} className="bg-white/10 p-3 rounded text-sm">
                  <div className="font-semibold">{entry.title}</div>
                  <div className="text-blue-200 text-xs">{entry.genre}</div>
                  <div className="flex justify-between items-center mt-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      entry.action === 'skipped' ? 'bg-red-500/30' : 'bg-green-500/30'
                    }`}>
                      {entry.action}
                    </span>
                    <span className="text-blue-200 text-xs">
                      {(entry.completionRate * 100).toFixed(0)}% played
                    </span>
                  </div>
                </div>
              ))}
              {listeningHistory.length === 0 && (
                <div className="text-blue-200 text-sm">No history yet. Start listening!</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
