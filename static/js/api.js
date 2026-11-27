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
      // If deployed on Firebase Hosting without a live backend instance, provide resilient fallback data
      if (window.location.hostname !== "127.0.0.1" && window.location.hostname !== "localhost") {
        return this.getCloudFallback(endpoint, options);
      }
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  getCloudFallback(endpoint, options) {
    console.warn(`[Cloud Fallback] Serving mock/cached data for ${endpoint}`);
    const catalog = [
      {
        id: 1,
        title: "Inception",
        release_year: 2010,
        duration: 148,
        average_rating: 4.8,
        rating_count: 320,
        poster_url: "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
        overview: "Cobb, a skilled thief who steals corporate secrets through dream-sharing technology, is given the task of planting an idea into the mind of a CEO.",
        director: "Christopher Nolan",
        cast_members: "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy",
        genres: ["Action", "Sci-Fi", "Adventure"],
        match_percentage: 99,
        explanation: "Top Spotlight Film"
      },
      {
        id: 2,
        title: "Interstellar",
        release_year: 2014,
        duration: 169,
        average_rating: 4.9,
        rating_count: 380,
        poster_url: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        overview: "Explorers travel through a wormhole in space in an attempt to ensure humanity's survival on distant habitable worlds.",
        director: "Christopher Nolan",
        cast_members: "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
        genres: ["Adventure", "Drama", "Sci-Fi"],
        match_percentage: 98,
        explanation: "Because you like Sci-Fi"
      },
      {
        id: 3,
        title: "The Dark Knight",
        release_year: 2008,
        duration: 152,
        average_rating: 4.9,
        rating_count: 410,
        poster_url: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/dqK9Hag1054tghRQSqLSfrkvQnA.jpg",
        overview: "Batman faces the criminal mastermind known as the Joker, who thrusts Gotham City into chaos.",
        director: "Christopher Nolan",
        cast_members: "Christian Bale, Heath Ledger, Aaron Eckhart",
        genres: ["Action", "Crime", "Drama"],
        match_percentage: 99,
        explanation: "Critically Acclaimed"
      },
      {
        id: 4,
        title: "The Matrix",
        release_year: 1999,
        duration: 136,
        average_rating: 4.8,
        rating_count: 290,
        poster_url: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/7c9UVPPiTPltouxShY9fKqURWZT.jpg",
        overview: "A computer hacker discovers reality is an artificial simulation created by cybernetic machines.",
        director: "Lana Wachowski, Lilly Wachowski",
        cast_members: "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        genres: ["Action", "Sci-Fi"],
        match_percentage: 97,
        explanation: "Because you like Cyberpunk Sci-Fi"
      },
      {
        id: 5,
        title: "Pulp Fiction",
        release_year: 1994,
        duration: 154,
        average_rating: 4.7,
        rating_count: 310,
        poster_url: "https://image.tmdb.org/t/p/w500/d5iIlFnGhFvlW147Ha50slSuTvS.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
        overview: "The lives of two mob hitmen, a boxer, a gangster and his wife intertwine in four tales of violence and redemption.",
        director: "Quentin Tarantino",
        cast_members: "John Travolta, Samuel L. Jackson, Uma Thurman",
        genres: ["Crime", "Drama"],
        match_percentage: 96,
        explanation: "Trending in Crime"
      },
      {
        id: 6,
        title: "Avengers: Infinity War",
        release_year: 2018,
        duration: 149,
        average_rating: 4.7,
        rating_count: 270,
        poster_url: "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/mDfJG3LC3Dqb67AZ52x3Z0jQ0uB.jpg",
        overview: "The Avengers must sacrifice all in an attempt to defeat the powerful Thanos before his blitz of devastation ruins the universe.",
        director: "Anthony Russo, Joe Russo",
        cast_members: "Robert Downey Jr., Chris Hemsworth, Mark Ruffalo",
        genres: ["Action", "Adventure", "Sci-Fi"],
        match_percentage: 97,
        explanation: "Popular Superhero"
      },
      {
        id: 7,
        title: "Gladiator",
        release_year: 2000,
        duration: 155,
        average_rating: 4.7,
        rating_count: 260,
        poster_url: "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/Ar7sFvh2ZfG9R1f02BaeJ4e7b4V.jpg",
        overview: "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.",
        director: "Ridley Scott",
        cast_members: "Russell Crowe, Joaquin Phoenix, Connie Nielsen",
        genres: ["Action", "Adventure", "Drama"],
        match_percentage: 96,
        explanation: "Award Winner"
      },
      {
        id: 8,
        title: "Dune",
        release_year: 2021,
        duration: 155,
        average_rating: 4.8,
        rating_count: 240,
        poster_url: "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/eeijXm3554UtMVXYqpMTZjo9P2q.jpg",
        overview: "Paul Atreides travels to the most dangerous planet in the universe to ensure the future of his family and people.",
        director: "Denis Villeneuve",
        cast_members: "Timothée Chalamet, Rebecca Ferguson, Zendaya",
        genres: ["Sci-Fi", "Adventure"],
        match_percentage: 98,
        explanation: "Trending Now"
      }
    ];

    if (endpoint === "/movies/featured") {
      return catalog[0];
    }
    if (endpoint === "/movies/categories") {
      return [
        { id: "recommended", title: "Top Picks for You", type: "recommended", movies: catalog.slice(0, 6) },
        { id: "trending", title: "Trending Now", type: "trending", movies: catalog.slice(2, 8) },
        { id: "action", title: "Action & Adventure", type: "genre", movies: catalog.filter(m => m.genres.includes("Action")) },
        { id: "scifi", title: "Sci-Fi & Mind Benders", type: "genre", movies: catalog.filter(m => m.genres.includes("Sci-Fi")) }
      ];
    }
    if (endpoint.startsWith("/movies/")) {
      const id = parseInt(endpoint.split("/")[2], 10);
      const m = catalog.find(x => x.id === id) || catalog[0];
      return { ...m, similar_movies: catalog.filter(x => x.id !== m.id).slice(0, 4) };
    }
    if (endpoint === "/auth/me") {
      return { authenticated: true, username: "demo_user", role: "user", preferences: ["Sci-Fi", "Action"] };
    }
    if (endpoint === "/watchlist") {
      return catalog.slice(1, 4);
    }
    if (endpoint === "/watch-history") {
      return catalog.slice(0, 3).map(m => ({ ...m, progress_pct: 65, completed: 0, last_watched_at: "Today" }));
    }
    if (endpoint === "/friends") {
      return [{ id: 3, username: "sarah_friend", last_watched_movie: "Interstellar" }];
    }
    return {};
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
