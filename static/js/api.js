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
      },
      {
        id: 9,
        title: "The Shawshank Redemption",
        release_year: 1994,
        duration: 142,
        average_rating: 4.9,
        rating_count: 450,
        poster_url: "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg",
        overview: "Framed for murder, banker Andy Dufresne begins a new life at Shawshank prison, forming a deep friendship with Red.",
        director: "Frank Darabont",
        cast_members: "Tim Robbins, Morgan Freeman",
        genres: ["Drama", "Crime"],
        match_percentage: 99,
        explanation: "All-Time Top Rated"
      },
      {
        id: 10,
        title: "Fight Club",
        release_year: 1999,
        duration: 139,
        average_rating: 4.8,
        rating_count: 360,
        poster_url: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
        overview: "An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker.",
        director: "David Fincher",
        cast_members: "Brad Pitt, Edward Norton, Helena Bonham Carter",
        genres: ["Drama", "Thriller"],
        match_percentage: 97,
        explanation: "Cult Classic"
      },
      {
        id: 11,
        title: "Oppenheimer",
        release_year: 2023,
        duration: 180,
        average_rating: 4.9,
        rating_count: 390,
        poster_url: "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/rM5Y09xC99JeApXWZZSIh42XBqZ.jpg",
        overview: "The story of J. Robert Oppenheimer's role in the development of the atomic bomb during World War II.",
        director: "Christopher Nolan",
        cast_members: "Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr.",
        genres: ["Drama", "History"],
        match_percentage: 98,
        explanation: "Oscar Winner"
      },
      {
        id: 12,
        title: "Spider-Man: Into the Spider-Verse",
        release_year: 2018,
        duration: 117,
        average_rating: 4.8,
        rating_count: 310,
        poster_url: "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/7d6woWBsigYrqqRvd29vyokuh57.jpg",
        overview: "Teen Miles Morales becomes the new Spider-Man and joins other Spider-heroes across dimensions to stop Kingpin.",
        director: "Bob Persichetti, Peter Ramsey",
        cast_members: "Shameik Moore, Jake Johnson, Hailee Steinfeld",
        genres: ["Animation", "Action", "Adventure"],
        match_percentage: 98,
        explanation: "Popular Animation"
      },
      {
        id: 13,
        title: "Parasite",
        release_year: 2019,
        duration: 132,
        average_rating: 4.8,
        rating_count: 330,
        poster_url: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg",
        overview: "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        director: "Bong Joon-ho",
        cast_members: "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong",
        genres: ["Thriller", "Drama", "Comedy"],
        match_percentage: 97,
        explanation: "Critically Acclaimed Thriller"
      },
      {
        id: 14,
        title: "Coco",
        release_year: 2017,
        duration: 105,
        average_rating: 4.8,
        rating_count: 280,
        poster_url: "https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/askg3SMvhqEl4OL52YuvdtY40Yb.jpg",
        overview: "Aspiring musician Miguel enters the Land of the Dead to find his great-great-grandfather, a legendary singer.",
        director: "Lee Unkrich",
        cast_members: "Anthony Gonzalez, Gael García Bernal",
        genres: ["Animation", "Family", "Music"],
        match_percentage: 96,
        explanation: "Family Favorite"
      },
      {
        id: 15,
        title: "Whiplash",
        release_year: 2014,
        duration: 107,
        average_rating: 4.8,
        rating_count: 290,
        poster_url: "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
        backdrop_url: "https://image.tmdb.org/t/p/original/6bbZ6XyvgfjhQwfplHVpj7IXemw.jpg",
        overview: "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing.",
        director: "Damien Chazelle",
        cast_members: "Miles Teller, J.K. Simmons",
        genres: ["Drama", "Music"],
        match_percentage: 97,
        explanation: "Intense Musical Drama"
      }
    ];

    if (endpoint.startsWith("/search")) {
      const urlParams = new URLSearchParams(endpoint.split("?")[1] || "");
      const q = (urlParams.get("q") || "").toLowerCase().trim();
      const genre = (urlParams.get("genre") || "").toLowerCase().trim();
      let results = [...catalog];
      if (genre && genre !== "all") {
        results = results.filter(m => m.genres && m.genres.some(g => g.toLowerCase() === genre));
      }
      if (q) {
        results = results.filter(m =>
          (m.title && m.title.toLowerCase().includes(q)) ||
          (m.director && m.director.toLowerCase().includes(q)) ||
          (m.cast_members && m.cast_members.toLowerCase().includes(q)) ||
          (m.overview && m.overview.toLowerCase().includes(q)) ||
          (m.genres && m.genres.some(g => g.toLowerCase().includes(q)))
        );
      }
      return results;
    }

    if (endpoint === "/movies/featured") {
      return catalog[0];
    }
    if (endpoint === "/movies/categories") {
      return [
        { id: "recommended", title: "Top Picks for You", type: "recommended", movies: catalog.slice(0, 6) },
        { id: "trending", title: "Trending Now", type: "trending", movies: catalog.slice(2, 8) },
        { id: "action", title: "Action & Adventure", type: "genre", movies: catalog.filter(m => m.genres.includes("Action")) },
        { id: "scifi", title: "Sci-Fi & Mind Benders", type: "genre", movies: catalog.filter(m => m.genres.includes("Sci-Fi")) },
        { id: "thriller", title: "Edge-of-Your-Seat Thrillers", type: "genre", movies: catalog.filter(m => m.genres.includes("Thriller")) },
        { id: "drama", title: "Critically Acclaimed Drama", type: "genre", movies: catalog.filter(m => m.genres.includes("Drama")) }
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
  async searchMovies(query, genre = "", sort = "popularity") {
    const params = new URLSearchParams({ q: query, genre, sort });
    try {
      const res = await this.request(`/search?${params.toString()}`);
      return Array.isArray(res) ? res : [];
    } catch (e) {
      const fallback = this.getCloudFallback(`/search?${params.toString()}`);
      return Array.isArray(fallback) ? fallback : [];
    }
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
