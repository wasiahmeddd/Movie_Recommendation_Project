/**
 * API Client for Movie Recommendation Platform.
 * Handles HTTP requests, JWT/Session tokens, and REST endpoints.
 */

const API_BASE = "/api";

const api = {
  getToken() {
    return localStorage.getItem("netflix_token") || "";
  },

  setToken(token) {
    if (token) {
      localStorage.setItem("netflix_token", token);
    } else {
      localStorage.removeItem("netflix_token");
    }
  },

  async request(endpoint, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth
  register(username, email, password) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, email, password })
    });
  },

  login(username, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },

  getMe() {
    return this.request("/auth/me");
  },

  logout() {
    return this.request("/auth/logout", { method: "POST" });
  },

  // Onboarding
  getAvailableGenres() {
    return this.request("/onboarding/genres");
  },

  saveOnboardingPreferences(genres) {
    return this.request("/onboarding/preferences", {
      method: "POST",
      body: JSON.stringify({ genres })
    });
  },

  // Discovery
  getFeaturedMovie() {
    return this.request("/movies/featured");
  },

  getCategories() {
    return this.request("/movies/categories");
  },

  getMovieDetails(movieId) {
    return this.request(`/movies/${movieId}`);
  },

  // Interactions & Analytics
  trackInteraction(movieId, interactionType, meta = {}) {
    return this.request("/interactions", {
      method: "POST",
      body: JSON.stringify({
        movie_id: movieId,
        interaction_type: interactionType,
        ...meta
      })
    });
  },

  // Watch Progress & History
  updateWatchProgress(movieId, progressPct) {
    return this.request("/watch-progress", {
      method: "POST",
      body: JSON.stringify({ movie_id: movieId, progress_pct: progressPct })
    });
  },

  getWatchHistory() {
    return this.request("/watch-history");
  },

  // Watchlist
  getWatchlist() {
    return this.request("/watchlist");
  },

  toggleWatchlist(movieId) {
    return this.request("/watchlist/toggle", {
      method: "POST",
      body: JSON.stringify({ movie_id: movieId })
    });
  },

  // Social
  getFriends() {
    return this.request("/friends");
  },

  searchFriends(query) {
    return this.request(`/friends/search?q=${encodeURIComponent(query)}`);
  },

  sendFriendRequest(targetUserId) {
    return this.request("/friends/request", {
      method: "POST",
      body: JSON.stringify({ target_user_id: targetUserId })
    });
  },

  // Search
  searchMovies(query, genre = "", sort = "popularity") {
    const params = new URLSearchParams({ q: query, genre, sort });
    return this.request(`/search?${params.toString()}`);
  },

  // Admin
  getAdminStats() {
    return this.request("/admin/stats");
  },

  getAdminMovies(page = 1, search = "") {
    return this.request(`/admin/movies?page=${page}&search=${encodeURIComponent(search)}`);
  },

  createMovie(movieData) {
    return this.request("/admin/movies", {
      method: "POST",
      body: JSON.stringify(movieData)
    });
  },

  deleteMovie(movieId) {
    return this.request(`/admin/movies/${movieId}`, {
      method: "DELETE"
    });
  }
};
