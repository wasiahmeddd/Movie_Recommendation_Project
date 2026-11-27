# CineStream • Intelligent Movie Discovery & Recommendation Platform

> **BMSCE AIML Skill Lab Review 2 — Production-Quality Movie Recommendation Platform**  
> A Netflix-inspired full-stack movie discovery platform featuring a **Hybrid Recommendation Engine**, real **MovieLens & TMDB dataset integration**, **user interaction tracking**, **onboarding preferences**, **Continue Watching progress**, **social friend discovery**, and an **administrative catalog portal**.

---

## 🌟 Executive Summary & What's New for Review 2

| Feature Category | First Review Prototype | Review 2 Upgraded Platform |
|---|---|---|
| **User Interface** | Terminal printouts & 3 static PNG plots | Full Netflix-inspired Single Page Web Platform (`#141414` dark theme, hero banner, responsive carousels, modals) |
| **Movie Dataset** | 15 hardcoded synthetic movies | **MovieLens (100K ratings, 1,200 top curated movies)** enriched with real high-res TMDB posters, backdrops, and overviews |
| **Recommendation Engine** | Basic TF-IDF on 15 items | **Intelligent Hybrid Engine**: Content-Based TF-IDF + User-User Collaborative Filtering + Interaction Boosts + Cold-Start Fallback |
| **Recommendation Explanations** | None | Dynamic badge explanations (*"Because you liked Inception"*, *"Matches your love for Sci-Fi"*, *"Watched by your friends"*) |
| **User Personalization** | None | Netflix-style genre onboarding (choose $\ge 3$ genres) persisted in database |
| **Interaction Tracking** | None | Real-time event logging: clicks, details views, watchlist additions, likes, dislikes, skips, and watch milestones |
| **Playback & History** | None | Interactive video simulation player with live scrubber, red progress bar, and dedicated **Continue Watching** row |
| **Social Recommendations** | None | Friend connection, shared activity feeds, and Web Contacts API detection with fallback |
| **Administration** | None | Protected Admin Portal to publish new movies with genre relationships, delete titles, and view platform metrics |
| **Database** | None (in-memory pandas) | Production **SQLite database (`movies.db`)** with foreign keys, indexes, and WAL mode |

---

## 🔑 Quick Demonstration Credentials

| Role | Username | Password | Notes |
|---|---|---|---|
| **Regular User** | `demo_user` | `user123` | Pre-seeded with genre preferences, watchlist, in-progress movies, and friend connection |
| **Administrator** | `admin` | `admin123` | Access to the ⚙ Admin Panel (publish movies, view live analytics, delete titles) |
| **Connected Friend** | `sarah_friend` | `user123` | Demonstrates social recommendation feed (*"Watched recently by sarah_friend"*) |

---

## 🚀 How to Run Locally

### 1. Requirements
- Python 3.10+
- Modern Web Browser (Chrome, Firefox, Edge, Safari)

### 2. Quick Launch

Open PowerShell / Terminal in this project directory:

```bash
# 1. (Optional) Run the automated 18-step test suite
python test_platform.py

# 2. Launch the web platform server
python server.py
```

Now open your browser and navigate to:  
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧠 Recommendation Engine Architecture

The platform implements a **Hybrid Multi-Objective Scoring Engine** combining:

### 1. Content-Based Filtering (CBF)
- Extracts rich textual features from movie titles, genres, overviews, directors, cast members, and tags.
- Tokenizes words with stop-word pruning.
- Computes **TF-IDF vector representations** and measures directional similarity via **Cosine Similarity**:
  $$\text{Sim}(A, B) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$
- Aggregates user profiles from movies rated $\ge 3.5$ or liked to score unseen items.

### 2. Collaborative Filtering (CF)
- Analyzes community ratings across MovieLens users.
- Computes centered cosine similarity / Pearson correlation between users:
  $$\text{sim}(u, v) = \frac{\sum_{i \in I_{uv}} (r_{u, i} - \bar{r}_u)(r_{v, i} - \bar{r}_v)}{\sqrt{\sum_{i \in I_{uv}} (r_{u, i} - \bar{r}_u)^2} \sqrt{\sum_{i \in I_{uv}} (r_{v, i} - \bar{r}_v)^2}}$$
- Predicts expected rating for unrated movies based on the user's nearest neighbors.

### 3. Real-Time Interaction Boosts
Signals captured from live user actions adjust ranking weights:
- **Watchlist addition**: $+0.25$
- **Like / High Rating**: $+0.35$
- **Completed Watch ($\ge 80\%$)**: $+0.30$
- **Click / Details View**: $+0.10$
- **Dislike**: $-0.60$ (hidden from candidate pool)
- **Immediate Skip ($< 10\%$ progress)**: $-0.20$

### 4. Cold-Start Strategy
For newly registered users without watch history:
- Matches user's chosen onboarding genres.
- Balances high average rating with rating volume via logarithmic popularity prior:
  $$\text{PopularityPrior} = 0.7 \times \left(\frac{\text{Rating}}{5.0}\right) + 0.3 \times \min\left(1.0, \frac{\ln(1 + \text{RatingCount})}{6.0}\right)$$

### 5. Final Hybrid Formula
$$\text{Score} = w_1 \cdot \text{GenreAffinity} + w_2 \cdot \text{ContentSim} + w_3 \cdot \text{CollabPred} + w_4 \cdot \text{QualityPrior} + \text{Boosts}$$

---

## 🗄 Database Schema (`movies.db`)

The SQLite database enforces foreign key constraints and indexed lookups:

* **`users`**: `id`, `username`, `email`, `password_hash`, `role`, `created_at`
* **`user_preferences`**: `id`, `user_id`, `genre`, `created_at` (minimum 3 enforced)
* **`movies`**: `id`, `movielens_id`, `tmdb_id`, `title`, `release_year`, `duration`, `overview`, `poster_url`, `backdrop_url`, `director`, `cast_members`, `average_rating`, `rating_count`, `tags`
* **`genres`**: `id`, `name`
* **`movie_genres`**: `movie_id`, `genre_id` (many-to-many relationship)
* **`ratings`**: `id`, `user_id`, `movie_id`, `rating` (0.5–5.0), `timestamp`
* **`user_interactions`**: `id`, `user_id`, `movie_id`, `interaction_type`, `watch_duration`, `completion_pct`, `recommendation_source`, `timestamp`
* **`watch_history`**: `id`, `user_id`, `movie_id`, `progress_pct`, `completed`, `last_watched_at`
* **`watchlist`**: `id`, `user_id`, `movie_id`, `added_at`
* **`friends`** & **`friend_requests`**: `id`, `user_id`, `friend_user_id`, `status`
* **`user_privacy_settings`**: `user_id`, `share_activity_with_friends`

---

## 📦 Dataset Download & Re-Import

The dataset script handles automatic downloading and parsing:

```bash
# To re-download MovieLens and re-seed database from scratch:
python datasets/download_and_import.py
```

If offline, the script checks if `datasets/ml-latest-small` exists and reuses local files without re-downloading.

---

## 🌐 Firebase Deployment Instructions

The project is structured to deploy to **Firebase Hosting**:

1. Install Firebase CLI (if not already present):
   ```bash
   npm install -g firebase-tools
   ```
2. Log in to Firebase:
   ```bash
   firebase login
   ```
3. Initialize / link your Firebase project:
   ```bash
   firebase use --add
   ```
4. Deploy the static streaming frontend:
   ```bash
   firebase deploy --only hosting
   ```
`firebase.json` is configured to serve the `static/` directory with client-side routing.

---

## 🧪 Testing and Quality Assurance

Execute the test suite to verify all endpoints and recommendation logic:

```bash
python test_platform.py
```

Expected output:
```
============================================================
 TEST RESULTS: 18/18 TESTS PASSED (100.0%)
============================================================
```

---

## 📋 Features Ready for Skill Lab Review 2 Demonstration

1. **Cinematic Homepage**: Open `http://127.0.0.1:5000` to show the hero banner, responsive carousels, and dark Netflix aesthetic.
2. **User Onboarding**: Click profile avatar -> "My Genre Preferences" -> pick 3+ genres -> observe how "Top Picks for You" immediately recalculates.
3. **Interactive Video Player**: Click "Play" on any movie -> scrub timeline -> click "Finish & Save" -> observe the updated red progress bar in "Continue Watching".
4. **Watchlist & History**: Add a movie with "+" -> check "My Watchlist" tab -> review "Viewing History" tab.
5. **Social Recommendations**: Sign in as `demo_user` -> open "Friends & Social" -> view connected friend `sarah_friend` -> view the "Popular Among Your Friends" carousel on the homepage.
6. **Administrator Portal**: Sign in as `admin` / `admin123` -> open "⚙ Admin Panel" in navigation -> view analytics widgets -> add a new movie -> verify it appears instantly in the catalog.
7. **Original Review 1 Prototype**: Run `python main.py` to demonstrate backward compatibility with the original 8-step console workflow.
