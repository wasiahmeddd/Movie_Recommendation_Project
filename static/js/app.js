/**
 * Main Application Controller
 * Handles Homepage, Carousels, Details Modal, Watchlist, Watch History, and Navigation.
 */

const app = {
  activeView: "home",
  activeDetailsMovie: null,

  async init() {
    this.setupNavbarScroll();
    this.setupSearch();
    await auth.init();
    this.loadHomePage();
  },

  setupNavbarScroll() {
    window.addEventListener("scroll", () => {
      const nav = document.getElementById("mainNavbar");
      if (window.scrollY > 40) {
        nav.classList.add("scrolled");
      } else {
        nav.classList.remove("scrolled");
      }
    });
  },

  setupSearch() {
    const input = document.getElementById("navSearchInput");
    const btn = document.getElementById("navSearchBtn");
    const suggestions = document.getElementById("searchSuggestions");
    let debounceTimer = null;

    const performSearch = async (query) => {
      if (!query || query.length < 1) {
        suggestions.classList.remove("active");
        suggestions.innerHTML = "";
        return;
      }

      suggestions.innerHTML = `<div style="padding: 12px; color: var(--text-muted); font-size: 13px;">Searching...</div>`;
      suggestions.classList.add("active");

      try {
        const results = await api.searchMovies(query);
        if (!results || results.length === 0) {
          suggestions.innerHTML = `<div style="padding: 12px; color: var(--text-muted); font-size: 13px;">No movies found for "${query}"</div>`;
        } else {
          suggestions.innerHTML = results.slice(0, 8).map(m => `
            <div class="suggestion-item" onclick="app.openDetails(${m.id})">
              <img src="${m.poster_url}" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=100&q=80'" />
              <div class="suggestion-info">
                <h4>${m.title}</h4>
                <p>${m.release_year} • ★ ${m.average_rating ? Number(m.average_rating).toFixed(1) : '4.5'} • ${m.genres ? m.genres.slice(0, 2).join(', ') : ''}</p>
              </div>
            </div>
          `).join("");
        }
        suggestions.classList.add("active");
      } catch (err) {
        console.error("Search error:", err);
        suggestions.innerHTML = `<div style="padding: 12px; color: #ff6b6b; font-size: 13px;">Search error. Try again.</div>`;
      }
    };

    input.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      debounceTimer = setTimeout(() => performSearch(query), 200);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        clearTimeout(debounceTimer);
        performSearch(input.value.trim());
      }
    });

    if (btn) {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        clearTimeout(debounceTimer);
        performSearch(input.value.trim());
        input.focus();
      });
    }

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".search-container")) {
        suggestions.classList.remove("active");
      }
    });
  },

  toggleProfileDropdown() {
    const dd = document.getElementById("profileDropdown");
    dd.classList.toggle("active");
  },

  switchView(viewName) {
    this.activeView = viewName;
    document.querySelectorAll(".page-view").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".nav-links a").forEach(el => el.classList.remove("active"));

    const navLink = document.getElementById(`nav-${viewName}`);
    if (navLink) navLink.classList.add("active");

    const targetEl = document.getElementById(`view-${viewName}`);
    if (targetEl) targetEl.classList.add("active");

    // Close dropdown
    const dd = document.getElementById("profileDropdown");
    if (dd) dd.classList.remove("active");

    if (viewName === "home") {
      this.loadHomePage();
    } else if (viewName === "watchlist") {
      this.loadWatchlistView();
    } else if (viewName === "history") {
      this.loadHistoryView();
    } else if (viewName === "friends") {
      social.loadFriendsView();
    } else if (viewName === "admin") {
      admin.loadAdminView();
    }
  },

  async loadHomePage() {
    document.getElementById("view-home").classList.add("active");
    this.loadFeaturedHero();
    this.loadCarousels();
  },

  async loadFeaturedHero() {
    try {
      const movie = await api.getFeaturedMovie();
      const hero = document.getElementById("heroBanner");
      const title = document.getElementById("heroTitle");
      const overview = document.getElementById("heroOverview");
      const match = document.getElementById("heroMatch");
      const rating = document.getElementById("heroRating");
      const year = document.getElementById("heroYear");
      const genres = document.getElementById("heroGenres");
      const playBtn = document.getElementById("heroPlayBtn");
      const infoBtn = document.getElementById("heroInfoBtn");
      const listBtn = document.getElementById("heroListBtn");

      if (movie.backdrop_url) {
        hero.style.backgroundImage = `url('${movie.backdrop_url}')`;
      }
      title.textContent = movie.title;
      overview.textContent = movie.overview;
      match.textContent = `${movie.match_percentage || 98}% Match`;
      rating.textContent = `★ ${movie.average_rating ? movie.average_rating.toFixed(1) : '4.5'}`;
      year.textContent = movie.release_year;
      genres.textContent = movie.genres ? movie.genres.join(" • ") : "";

      playBtn.onclick = () => player.open(movie, 0);
      infoBtn.onclick = () => this.openDetails(movie.id);
      listBtn.onclick = async () => {
        const res = await api.toggleWatchlist(movie.id);
        listBtn.textContent = res.in_watchlist ? "✓ In Watchlist" : "+ My List";
      };
    } catch (err) {
      console.error("Hero load error:", err);
    }
  },

  async loadCarousels() {
    const container = document.getElementById("carouselsContainer");
    container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-secondary);">Loading cinematic catalog and intelligent recommendations...</div>`;

    try {
      const categories = await api.getCategories();
      container.innerHTML = "";

      categories.forEach(cat => {
        if (!cat.movies || cat.movies.length === 0) return;

        const section = document.createElement("div");
        section.className = "carousel-section";

        section.innerHTML = `
          <div class="carousel-header">
            <h3 class="carousel-title">
              ${cat.title}
              <span class="carousel-explanation">${cat.movies[0].explanation ? `— ${cat.movies[0].explanation}` : ''}</span>
            </h3>
          </div>
          <div class="carousel-track-wrapper">
            <button class="carousel-arrow left" onclick="app.scrollCarousel(this, -1)">‹</button>
            <div class="carousel-track" id="track-${cat.id}">
              ${cat.movies.map(m => this.renderMovieCard(m, cat.type === "continue_watching")).join("")}
            </div>
            <button class="carousel-arrow right" onclick="app.scrollCarousel(this, 1)">›</button>
          </div>
        `;
        container.appendChild(section);
      });
    } catch (err) {
      container.innerHTML = `<div style="color: #ff6b6b; padding: 30px;">Error loading categories: ${err.message}</div>`;
    }
  },

  renderMovieCard(movie, isContinueWatching = false) {
    const genresStr = movie.genres ? movie.genres.slice(0, 2).join(", ") : "";
    return `
      <div class="movie-card" onclick="app.openDetails(${movie.id})">
        <img class="movie-poster" src="${movie.poster_url}" alt="${movie.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80'" />
        
        ${isContinueWatching && movie.progress_pct ? `
          <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${movie.progress_pct}%"></div>
          </div>
        ` : ''}

        <div class="movie-card-overlay">
          <div class="card-title">${movie.title}</div>
          <div class="card-meta">
            <span class="card-match">${movie.match_percentage || 95}% Match</span>
            <span>${movie.release_year}</span>
          </div>
          <div class="card-genres">${genresStr}</div>
          <div class="card-actions" onclick="event.stopPropagation()">
            <button class="icon-btn primary" title="Play" onclick="player.open(${JSON.stringify(movie).replace(/"/g, '&quot;')}, ${movie.progress_pct || 0})">▶</button>
            <button class="icon-btn" title="Add to Watchlist" onclick="app.toggleCardWatchlist(this, ${movie.id})">+</button>
            <button class="icon-btn" title="Like" onclick="app.handleLike(this, ${movie.id})">👍</button>
            <button class="icon-btn" title="Dislike" onclick="app.handleDislike(this, ${movie.id})">👎</button>
          </div>
        </div>
      </div>
    `;
  },

  scrollCarousel(button, direction) {
    const wrapper = button.parentElement;
    const track = wrapper.querySelector(".carousel-track");
    const scrollAmount = track.clientWidth * 0.75 * direction;
    track.scrollBy({ left: scrollAmount, behavior: "smooth" });
  },

  async openDetails(movieId) {
    const modal = document.getElementById("detailsModal");
    tracker.trackViewDetails(movieId);

    try {
      const movie = await api.getMovieDetails(movieId);
      this.activeDetailsMovie = movie;

      const hero = document.getElementById("modalHero");
      const title = document.getElementById("modalTitle");
      const match = document.getElementById("modalMatch");
      const year = document.getElementById("modalYear");
      const duration = document.getElementById("modalDuration");
      const overview = document.getElementById("modalOverview");
      const director = document.getElementById("modalDirector");
      const cast = document.getElementById("modalCast");
      const genres = document.getElementById("modalGenres");
      const playBtn = document.getElementById("modalPlayBtn");
      const listBtn = document.getElementById("modalListBtn");
      const similarTrack = document.getElementById("modalSimilarTrack");
      const explanationBanner = document.getElementById("modalExplanationBanner");

      if (movie.backdrop_url) {
        hero.style.backgroundImage = `url('${movie.backdrop_url}')`;
      }
      title.textContent = movie.title;
      match.textContent = `${movie.average_rating ? Math.round(movie.average_rating * 20) : 95}% Match`;
      year.textContent = movie.release_year;
      duration.textContent = `${movie.duration || 110}m`;
      overview.textContent = movie.overview;
      director.textContent = movie.director || "N/A";
      cast.textContent = movie.cast_members || "N/A";
      genres.textContent = movie.genres ? movie.genres.join(", ") : "N/A";

      explanationBanner.textContent = `🎯 Recommended for your taste profile • High correlation in ${movie.genres ? movie.genres[0] : 'Drama'}`;

      listBtn.textContent = movie.in_watchlist ? "✓ In Watchlist" : "+ Add to Watchlist";
      listBtn.onclick = async () => {
        const res = await api.toggleWatchlist(movie.id);
        listBtn.textContent = res.in_watchlist ? "✓ In Watchlist" : "+ Add to Watchlist";
      };

      playBtn.onclick = () => {
        this.closeDetails();
        player.open(movie, movie.watch_progress || 0);
      };

      // Similar movies row
      if (movie.similar_movies && movie.similar_movies.length > 0) {
        similarTrack.innerHTML = movie.similar_movies.map(m => this.renderMovieCard(m)).join("");
      } else {
        similarTrack.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">No direct similar movies found.</p>`;
      }

      modal.classList.add("active");
    } catch (err) {
      alert("Error loading movie details: " + err.message);
    }
  },

  closeDetails() {
    document.getElementById("detailsModal").classList.remove("active");
    this.activeDetailsMovie = null;
  },

  async toggleCardWatchlist(button, movieId) {
    try {
      const res = await api.toggleWatchlist(movieId);
      button.textContent = res.in_watchlist ? "✓" : "+";
      button.classList.toggle("active", res.in_watchlist);
    } catch (e) {
      alert("Watchlist update failed: " + e.message);
    }
  },

  async handleLike(button, movieId) {
    tracker.trackLike(movieId);
    button.classList.add("active");
    button.style.color = "var(--accent-green)";
  },

  async handleDislike(button, movieId) {
    tracker.trackDislike(movieId);
    button.classList.add("active");
    button.style.color = "var(--netflix-red)";
  },

  // Watchlist View
  async loadWatchlistView() {
    const grid = document.getElementById("watchlistGrid");
    grid.innerHTML = `<div style="color: var(--text-secondary); padding: 30px;">Loading your saved watchlist...</div>`;

    try {
      const items = await api.getWatchlist();
      if (!items || items.length === 0) {
        grid.innerHTML = `<div style="color: var(--text-muted); font-size: 15px; padding: 40px; text-align: center;">Your watchlist is empty. Explore the homepage and tap "+" to save movies for later!</div>`;
        return;
      }
      grid.innerHTML = items.map(m => this.renderMovieCard(m)).join("");
    } catch (err) {
      grid.innerHTML = `<div style="color: #ff6b6b;">Error: ${err.message}</div>`;
    }
  },

  // History View
  async loadHistoryView() {
    const list = document.getElementById("historyList");
    list.innerHTML = `<div style="color: var(--text-secondary); padding: 30px;">Loading viewing history...</div>`;

    try {
      const history = await api.getWatchHistory();
      if (!history || history.length === 0) {
        list.innerHTML = `<div style="color: var(--text-muted); font-size: 15px; padding: 40px; text-align: center;">No movies watched yet. Click Play on any movie to start watching!</div>`;
        return;
      }

      list.innerHTML = history.map(h => `
        <div style="display: flex; gap: 16px; background: #202020; padding: 14px; border-radius: 6px; margin-bottom: 12px; align-items: center;">
          <img src="${h.poster_url}" style="width: 60px; height: 90px; object-fit: cover; border-radius: 4px;" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=100&q=80'" />
          <div style="flex: 1;">
            <h4 style="font-size: 16px; margin-bottom: 4px;">${h.title} (${h.release_year})</h4>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
              ${h.completed ? '<span style="color: var(--accent-green); font-weight: bold;">✓ Completed</span>' : `<span style="color: var(--netflix-red);">Watching (${Math.round(h.progress_pct)}%)</span>`} • ${h.last_watched_at}
            </div>
            <div style="height: 4px; background: #333; border-radius: 2px; width: 200px; overflow: hidden;">
              <div style="height: 100%; background: var(--netflix-red); width: ${h.progress_pct}%;"></div>
            </div>
          </div>
          <button class="btn btn-secondary" onclick="player.open(${JSON.stringify(h).replace(/"/g, '&quot;')}, ${h.progress_pct || 0})">Resume ▶</button>
        </div>
      `).join("");
    } catch (err) {
      list.innerHTML = `<div style="color: #ff6b6b;">Error: ${err.message}</div>`;
    }
  }
};

window.addEventListener("DOMContentLoaded", () => {
  app.init();
});
