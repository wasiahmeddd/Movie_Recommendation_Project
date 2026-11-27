/**
 * Onboarding Genre Preferences Module
 * Requires selecting at least 3 genres with visual cards and dynamic counter.
 */

const onboarding = {
  selectedGenres: new Set(),

  STANDARD_GENRES: [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Science Fiction", "Thriller", "War", "Western"
  ],

  async show() {
    const modal = document.getElementById("onboardingModal");
    const container = document.getElementById("genresGridContainer");
    this.selectedGenres.clear();

    // Populate existing preferences if any
    if (auth.currentUser && auth.currentUser.preferences) {
      auth.currentUser.preferences.forEach(g => this.selectedGenres.add(g));
    }

    container.innerHTML = "";
    this.STANDARD_GENRES.forEach(genre => {
      const tile = document.createElement("div");
      tile.className = "genre-tile" + (this.selectedGenres.has(genre) ? " selected" : "");
      tile.textContent = genre;
      tile.onclick = () => this.toggleGenre(genre, tile);
      container.appendChild(tile);
    });

    this.updateCounter();
    modal.classList.add("active");
  },

  hide() {
    const modal = document.getElementById("onboardingModal");
    modal.classList.remove("active");
  },

  toggleGenre(genre, element) {
    if (this.selectedGenres.has(genre)) {
      this.selectedGenres.delete(genre);
      element.classList.remove("selected");
    } else {
      this.selectedGenres.add(genre);
      element.classList.add("selected");
    }
    this.updateCounter();
  },

  updateCounter() {
    const countDisplay = document.getElementById("onboardingCountDisplay");
    const submitBtn = document.getElementById("onboardingSubmitBtn");
    const count = this.selectedGenres.size;

    countDisplay.textContent = `${count} of 3 selected`;
    if (count >= 3) {
      countDisplay.style.color = "var(--accent-green)";
      submitBtn.disabled = false;
      submitBtn.style.opacity = "1";
      submitBtn.style.cursor = "pointer";
    } else {
      countDisplay.style.color = "var(--text-secondary)";
      submitBtn.disabled = true;
      submitBtn.style.opacity = "0.4";
      submitBtn.style.cursor = "not-allowed";
    }
  },

  async submit() {
    if (this.selectedGenres.size < 3) {
      alert("Please select at least 3 genres to proceed.");
      return;
    }

    try {
      await api.saveOnboardingPreferences(Array.from(this.selectedGenres));
      this.hide();
      // Refresh user and home page to render personalized recommendations
      await auth.init();
      app.loadHomePage();
    } catch (err) {
      alert("Failed to save preferences: " + err.message);
    }
  }
};
