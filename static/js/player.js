/**
 * Video Player Simulation Module
 * Simulates playback, scrub timeline, tracks 25%, 50%, 75%, 100% milestones,
 * and updates live progress in "Continue Watching".
 */

const player = {
  activeMovie: null,
  currentSeconds: 0,
  totalSeconds: 7200, // 120 minutes default
  isPlaying: false,
  timerInterval: null,
  lastRecordedMilestone: 0,

  open(movie, startProgress = 0) {
    this.activeMovie = movie;
    this.totalSeconds = (movie.duration || 110) * 60;
    this.currentSeconds = Math.floor((startProgress / 100) * this.totalSeconds);
    this.isPlaying = true;
    this.lastRecordedMilestone = startProgress;

    const modal = document.getElementById("playerModal");
    const titleEl = document.getElementById("playerMovieTitle");
    const scrubber = document.getElementById("playerScrubber");

    if (titleEl) titleEl.textContent = movie.title;
    if (scrubber) {
      scrubber.max = this.totalSeconds;
      scrubber.value = this.currentSeconds;
    }

    modal.classList.add("active");
    this.updateTimeDisplay();
    this.startPlayback();

    tracker.trackClick(movie.id, "player_start");
  },

  close() {
    this.pausePlayback();
    // Save final progress
    if (this.activeMovie) {
      const pct = Math.round((this.currentSeconds / this.totalSeconds) * 100);
      tracker.trackProgress(this.activeMovie.id, pct);
    }
    const modal = document.getElementById("playerModal");
    modal.classList.remove("active");
    this.activeMovie = null;

    // Refresh homepage to show updated progress bar in Continue Watching
    app.loadHomePage();
  },

  startPlayback() {
    this.isPlaying = true;
    const playPauseBtn = document.getElementById("playerPlayPauseBtn");
    if (playPauseBtn) playPauseBtn.textContent = "⏸ Pause";

    if (this.timerInterval) clearInterval(this.timerInterval);
    this.timerInterval = setInterval(() => {
      if (this.currentSeconds < this.totalSeconds) {
        this.currentSeconds += 3; // fast forward simulation
        this.updateTimeDisplay();
        this.checkMilestones();
      } else {
        this.pausePlayback();
      }
    }, 500);
  },

  pausePlayback() {
    this.isPlaying = false;
    const playPauseBtn = document.getElementById("playerPlayPauseBtn");
    if (playPauseBtn) playPauseBtn.textContent = "▶ Play";
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  togglePlayPause() {
    if (this.isPlaying) {
      this.pausePlayback();
    } else {
      this.startPlayback();
    }
  },

  seekTo(seconds) {
    this.currentSeconds = Math.min(this.totalSeconds, Math.max(0, parseInt(seconds, 10)));
    this.updateTimeDisplay();
    this.checkMilestones();
  },

  updateTimeDisplay() {
    const curTimeEl = document.getElementById("playerCurrentTime");
    const scrubber = document.getElementById("playerScrubber");
    if (curTimeEl) curTimeEl.textContent = this.formatTime(this.currentSeconds);
    if (scrubber) scrubber.value = this.currentSeconds;
  },

  checkMilestones() {
    const pct = Math.round((this.currentSeconds / this.totalSeconds) * 100);
    // Send milestone progress updates to backend at 25%, 50%, 75%, 100%
    if (pct - this.lastRecordedMilestone >= 10 || pct >= 95) {
      this.lastRecordedMilestone = pct;
      if (this.activeMovie) {
        tracker.trackProgress(this.activeMovie.id, pct);
      }
    }
  },

  formatTime(totalSecs) {
    const m = Math.floor(totalSecs / 60);
    const s = totalSecs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }
};
