/**
 * User Interaction Tracking Module
 * Captures user behaviour: clicks, details views, watch progress,
 * skips, likes, dislikes, and impressions without spamming duplicate events.
 */

const tracker = {
  recordedImpressions: new Set(),

  trackClick(movieId, source = "carousel") {
    api.trackInteraction(movieId, "click", { recommendation_source: source });
  },

  trackViewDetails(movieId, source = "modal") {
    api.trackInteraction(movieId, "view_details", { recommendation_source: source });
  },

  trackWatchlistAdd(movieId) {
    api.trackInteraction(movieId, "watchlist_add");
  },

  trackLike(movieId) {
    api.trackInteraction(movieId, "like");
  },

  trackDislike(movieId) {
    api.trackInteraction(movieId, "dislike");
  },

  trackSkip(movieId, completionPct) {
    api.trackInteraction(movieId, "skip", { completion_pct: completionPct });
  },

  trackProgress(movieId, progressPct) {
    api.updateWatchProgress(movieId, progressPct);
  }
};
