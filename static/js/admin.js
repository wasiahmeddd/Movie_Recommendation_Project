/**
 * Administrative Panel Module
 * Manages movies (create, view, delete) and displays platform analytics.
 */

const admin = {
  currentPage: 1,

  async loadAdminView() {
    if (!auth.currentUser || auth.currentUser.role !== "admin") {
      alert("Administrator access required.");
      app.switchView("home");
      return;
    }

    this.loadStats();
    this.loadMoviesTable();
  },

  async loadStats() {
    try {
      const stats = await api.getAdminStats();
      const elMovies = document.getElementById("adminStatMovies");
      const elUsers = document.getElementById("adminStatUsers");
      const elRatings = document.getElementById("adminStatRatings");
      const elInteractions = document.getElementById("adminStatInteractions");

      if (elMovies) elMovies.textContent = stats.total_movies;
      if (elUsers) elUsers.textContent = stats.total_users;
      if (elRatings) elRatings.textContent = stats.total_ratings;
      if (elInteractions) elInteractions.textContent = stats.total_interactions;
    } catch (err) {
      console.error("Admin stats failed:", err);
    }
  },

  async loadMoviesTable(page = 1, search = "") {
    this.currentPage = page;
    const tbody = document.getElementById("adminMoviesTbody");
    if (!tbody) return;

    try {
      const movies = await api.getAdminMovies(page, search);
      tbody.innerHTML = movies.map(m => `
        <tr>
          <td>${m.id}</td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <img src="${m.poster_url}" style="width: 28px; height: 40px; object-fit: cover; border-radius: 2px;" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=100&q=80'" />
              <strong>${m.title}</strong>
            </div>
          </td>
          <td>${m.release_year}</td>
          <td>${m.genres ? m.genres.slice(0, 2).join(", ") : 'N/A'}</td>
          <td>★ ${m.average_rating ? m.average_rating.toFixed(1) : '0.0'}</td>
          <td>
            <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; background: #c0392b;" onclick="admin.deleteMovie(${m.id})">Delete</button>
          </td>
        </tr>
      `).join("");
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="6" style="color: #ff6b6b;">Error loading movies: ${e.message}</td></tr>`;
    }
  },

  async handleAddMovie(event) {
    event.preventDefault();
    const title = document.getElementById("adminMovieTitle").value;
    const release_year = parseInt(document.getElementById("adminMovieYear").value, 10);
    const duration = parseInt(document.getElementById("adminMovieDuration").value, 10);
    const rating = parseFloat(document.getElementById("adminMovieRating").value);
    const director = document.getElementById("adminMovieDirector").value;
    const cast_members = document.getElementById("adminMovieCast").value;
    const overview = document.getElementById("adminMovieOverview").value;
    const poster_url = document.getElementById("adminMoviePoster").value;
    const backdrop_url = document.getElementById("adminMovieBackdrop").value;
    const genres = document.getElementById("adminMovieGenres").value.split(",").map(g => g.strip ? g.strip() : g.trim()).filter(Boolean);

    try {
      await api.createMovie({
        title, release_year, duration, rating, director, cast_members,
        overview, poster_url, backdrop_url, genres
      });
      alert(`Movie "${title}" added successfully! It is now live in the catalog and recommendation engine.`);
      document.getElementById("adminAddMovieForm").reset();
      this.loadStats();
      this.loadMoviesTable();
    } catch (e) {
      alert("Failed to add movie: " + e.message);
    }
  },

  async deleteMovie(movieId) {
    if (!confirm(`Are you sure you want to delete movie ID ${movieId}?`)) return;
    try {
      await api.deleteMovie(movieId);
      alert("Movie deleted successfully.");
      this.loadStats();
      this.loadMoviesTable(this.currentPage);
    } catch (e) {
      alert("Delete failed: " + e.message);
    }
  }
};
