"""
Flask REST API Server for Movie Recommendation Platform.
Provides endpoints for Authentication, Onboarding Preferences, Discovery Carousels,
Hybrid Recommendations, Interaction Tracking, Watchlist, Continue Watching,
Social Friends Discovery, Search, and Admin Movie Management.
"""

import os
import json
import secrets
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from database import get_db_connection, hash_password
from recommendation_engine import engine

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# In-memory session store (token -> user_id)
# Tokens persist for server lifetime; client stores in localStorage
ACTIVE_SESSIONS = {}


def generate_token():
    return secrets.token_hex(24)


def get_current_user():
    """Extracts authenticated user from Authorization header or cookie."""
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.args.get("token"):
        token = request.args.get("token")

    if not token or token not in ACTIVE_SESSIONS:
        return None

    user_id = ACTIVE_SESSIONS[token]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return f(user, *args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get("role") != "admin":
            return jsonify({"error": "Admin privileges required"}), 403
        return f(user, *args, **kwargs)
    return decorated_function


# ============================================================
# 1. AUTHENTICATION & SESSION ROUTES
# ============================================================

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not username or len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email address required"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'user')",
            (username, email, pw_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        token = generate_token()
        ACTIVE_SESSIONS[token] = user_id

        # Initialize privacy settings
        cursor.execute("INSERT OR IGNORE INTO user_privacy_settings (user_id, share_activity_with_friends) VALUES (?, 1)", (user_id,))
        conn.commit()
        conn.close()

        return jsonify({
            "message": "User registered successfully",
            "token": token,
            "user": {"id": user_id, "username": username, "email": email, "role": "user", "has_onboarded": False}
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({"error": "Username or email already exists"}), 409


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("username", "").strip() # can be username or email
    password = data.get("password", "").strip()

    if not identifier or not password:
        return jsonify({"error": "Please provide username/email and password"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(password)
    cursor.execute("""
        SELECT id, username, email, role FROM users
        WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)) AND password_hash = ?
    """, (identifier, identifier, pw_hash))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Invalid username or password"}), 401

    user_dict = dict(user)
    # Check if user has chosen preferences (onboarding done)
    cursor.execute("SELECT COUNT(*) AS count FROM user_preferences WHERE user_id = ?", (user_dict["id"],))
    pref_count = cursor.fetchone()["count"]
    conn.close()

    token = generate_token()
    ACTIVE_SESSIONS[token] = user_dict["id"]

    user_dict["has_onboarded"] = pref_count >= 3
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user_dict
    })


@app.route("/api/auth/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT genre FROM user_preferences WHERE user_id = ?", (user["id"],))
    prefs = [r["genre"] for r in cursor.fetchall()]
    conn.close()

    user["preferences"] = prefs
    user["has_onboarded"] = len(prefs) >= 3
    user["authenticated"] = True
    return jsonify(user)


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        ACTIVE_SESSIONS.pop(token, None)
    return jsonify({"message": "Logged out successfully"})


# ============================================================
# 2. ONBOARDING & PREFERENCES ROUTES
# ============================================================

@app.route("/api/onboarding/genres", methods=["GET"])
def list_available_genres():
    """List of selectable genres for onboarding."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM genres ORDER BY name ASC")
    genres = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(genres)


@app.route("/api/onboarding/preferences", methods=["POST"])
@login_required
def save_preferences(user):
    data = request.get_json() or {}
    genres = data.get("genres", [])
    if not isinstance(genres, list) or len(genres) < 3:
        return jsonify({"error": "Please select at least 3 genres to personalize your experience"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # Replace existing preferences
    cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user["id"],))
    for g in genres:
        cursor.execute("INSERT OR IGNORE INTO user_preferences (user_id, genre) VALUES (?, ?)", (user["id"], g.strip()))
    conn.commit()
    conn.close()

    return jsonify({"message": "Preferences saved successfully", "count": len(genres)})


# ============================================================
# 3. DISCOVERY & HOMEPAGE CATEGORIES
# ============================================================

@app.route("/api/movies/featured", methods=["GET"])
def get_featured_movie():
    """Returns a prominent cinematic blockbuster for the hero banner."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Look for Inception, Interstellar, or highest rated movie with backdrop
    cursor.execute("""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE m.backdrop_url IS NOT NULL AND m.backdrop_url != ''
        GROUP BY m.id
        ORDER BY (m.title IN ('Inception', 'Interstellar', 'The Dark Knight')) DESC, m.rating_count DESC
        LIMIT 1
    """)
    featured = cursor.fetchone()
    conn.close()

    if not featured:
        return jsonify({"error": "No featured movie available"}), 404

    f_dict = dict(featured)
    f_dict["genres"] = [g.strip() for g in (f_dict.get("genres_list") or "").split(",") if g.strip()]
    f_dict["match_percentage"] = 99
    return jsonify(f_dict)


@app.route("/api/movies/categories", methods=["GET"])
def get_categories():
    """
    Returns populated movie carousels for the homepage:
    - Continue Watching (if logged in)
    - Recommended For You (Hybrid Engine)
    - Trending Now
    - Top Rated
    - Genre Rows (Action, Sci-Fi, Thriller, Horror, Romance, Comedy, Animation, Drama, Crime)
    - Friends Activity (Social)
    - Recently Added
    """
    user = get_current_user()
    user_id = user["id"] if user else 2 # default to demo user if anonymous visitor

    conn = get_db_connection()
    cursor = conn.cursor()

    categories = []

    # Helper function to format movie rows
    def format_rows(rows, explanation="Trending Now", match_base=94):
        items = []
        for r in rows:
            d = dict(r)
            d["genres"] = [g.strip() for g in (d.get("genres_list") or "").split(",") if g.strip()]
            d["match_percentage"] = d.get("match_percentage", match_base)
            d["explanation"] = d.get("explanation", explanation)
            items.append(d)
        return items

    # 1. CONTINUE WATCHING (User's in-progress movies with progress bar)
    if user:
        cursor.execute("""
            SELECT m.*, wh.progress_pct, wh.completed,
                   GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM watch_history wh
            JOIN movies m ON wh.movie_id = m.id
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE wh.user_id = ? AND wh.completed = 0 AND wh.progress_pct > 5.0
            GROUP BY m.id
            ORDER BY wh.last_watched_at DESC
            LIMIT 10
        """, (user_id,))
        cw_rows = cursor.fetchall()
        if cw_rows:
            categories.append({
                "id": "continue_watching",
                "title": "Continue Watching for " + user["username"],
                "type": "continue_watching",
                "movies": format_rows(cw_rows, "Continue Watching", 98)
            })

    # 2. RECOMMENDED FOR YOU (Hybrid Engine with real personalized explanations)
    recs = engine.recommend_for_user(user_id=user_id, top_n=14)
    if recs:
        categories.append({
            "id": "recommended_for_you",
            "title": "Top Picks for You",
            "type": "recommended",
            "movies": recs
        })

    # 3. SOCIAL RECOMMENDATIONS (Watched by your friends)
    if user:
        social_recs = engine.get_social_recommendations(user_id=user_id, top_n=10)
        if social_recs:
            categories.append({
                "id": "popular_among_friends",
                "title": "Popular Among Your Friends",
                "type": "social",
                "movies": social_recs
            })

    # 4. TRENDING NOW (Highest interaction and rating volume)
    cursor.execute("""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        GROUP BY m.id
        ORDER BY m.rating_count DESC, m.average_rating DESC
        LIMIT 14
    """)
    trending_rows = cursor.fetchall()
    categories.append({
        "id": "trending_now",
        "title": "Trending Now",
        "type": "trending",
        "movies": format_rows(trending_rows, "Trending Now", 96)
    })

    # 5. TOP RATED MOVIES
    cursor.execute("""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE m.rating_count >= 50
        GROUP BY m.id
        ORDER BY m.average_rating DESC, m.rating_count DESC
        LIMIT 14
    """)
    top_rows = cursor.fetchall()
    categories.append({
        "id": "top_rated",
        "title": "Critically Acclaimed & Top Rated",
        "type": "top_rated",
        "movies": format_rows(top_rows, "Critically Acclaimed", 97)
    })

    # 6. GENRE CATEGORIES
    genre_sections = [
        ("Action & Adventure", ["Action", "Adventure"]),
        ("Sci-Fi & Mind Benders", ["Sci-Fi", "Science Fiction"]),
        ("Edge-of-Your-Seat Thrillers", ["Thriller"]),
        ("Horror & Dark Cinema", ["Horror"]),
        ("Romantic Favourites", ["Romance"]),
        ("Comedies", ["Comedy"]),
        ("Crime & Mystery", ["Crime", "Mystery"]),
        ("Animation & Family", ["Animation", "Family"]),
        ("Historical & War", ["History", "War"]),
    ]

    for cat_title, genre_names in genre_sections:
        placeholders = ",".join("?" for _ in genre_names)
        cursor.execute(f"""
            SELECT m.*, GROUP_CONCAT(DISTINCT g.name) AS genres_list
            FROM movies m
            JOIN movie_genres mg ON m.id = mg.movie_id
            JOIN genres g ON mg.genre_id = g.id
            WHERE g.name IN ({placeholders})
            GROUP BY m.id
            ORDER BY m.rating_count DESC, m.average_rating DESC
            LIMIT 14
        """, genre_names)
        g_rows = cursor.fetchall()
        if g_rows:
            categories.append({
                "id": cat_title.lower().replace(" ", "_").replace("&", "and"),
                "title": cat_title,
                "type": "genre",
                "movies": format_rows(g_rows, f"Top in {cat_title}", 92)
            })

    # 7. RECENTLY ADDED
    cursor.execute("""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        GROUP BY m.id
        ORDER BY m.id DESC
        LIMIT 14
    """)
    recent_rows = cursor.fetchall()
    categories.append({
        "id": "recently_added",
        "title": "Recently Added to Catalog",
        "type": "recent",
        "movies": format_rows(recent_rows, "Recently Added", 90)
    })

    conn.close()
    return jsonify(categories)


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie_details(movie_id):
    """Detailed metadata for a movie including cast, director, and similar movies."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE m.id = ?
        GROUP BY m.id
    """, (movie_id,))
    movie = cursor.fetchone()

    if not movie:
        conn.close()
        return jsonify({"error": "Movie not found"}), 404

    m_dict = dict(movie)
    m_dict["genres"] = [g.strip() for g in (m_dict.get("genres_list") or "").split(",") if g.strip()]

    # Check if in watchlist or watch history for current user
    user = get_current_user()
    m_dict["in_watchlist"] = False
    m_dict["watch_progress"] = 0.0

    if user:
        cursor.execute("SELECT id FROM watchlist WHERE user_id = ? AND movie_id = ?", (user["id"], movie_id))
        m_dict["in_watchlist"] = cursor.fetchone() is not None
        cursor.execute("SELECT progress_pct FROM watch_history WHERE user_id = ? AND movie_id = ?", (user["id"], movie_id))
        wh = cursor.fetchone()
        if wh:
            m_dict["watch_progress"] = wh["progress_pct"]

    # Top similar movies using Content-Based TF-IDF engine
    similar_ids_scores = engine.content_model.get_similar_movies(movie_id, top_n=6)
    similar_movies = []
    for sim_id, score in similar_ids_scores:
        cursor.execute("""
            SELECT m.id, m.title, m.release_year, m.average_rating, m.poster_url, m.backdrop_url,
                   GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.id = ?
            GROUP BY m.id
        """, (sim_id,))
        sim_row = cursor.fetchone()
        if sim_row:
            s_dict = dict(sim_row)
            s_dict["genres"] = [g.strip() for g in (s_dict.get("genres_list") or "").split(",") if g.strip()]
            s_dict["match_percentage"] = int(min(99, max(75, round(score * 100 + 40))))
            s_dict["explanation"] = f"Similar to {m_dict['title']}"
            similar_movies.append(s_dict)

    m_dict["similar_movies"] = similar_movies
    conn.close()
    return jsonify(m_dict)


# ============================================================
# 4. USER INTERACTION TRACKING
# ============================================================

@app.route("/api/interactions", methods=["POST"])
@login_required
def track_interaction(user):
    """
    Logs meaningful user interactions:
    'click', 'view_details', 'watchlist_add', 'watch_start', 'watch_progress',
    'complete', 'like', 'dislike', 'skip', 'impression'
    """
    data = request.get_json() or {}
    movie_id = data.get("movie_id")
    interaction_type = data.get("interaction_type")
    watch_duration = int(data.get("watch_duration", 0))
    completion_pct = float(data.get("completion_pct", 0.0))
    source = data.get("recommendation_source", "direct")
    session_id = data.get("session_id", "web")

    if not movie_id or not interaction_type:
        return jsonify({"error": "movie_id and interaction_type are required"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM movies WHERE id = ?", (movie_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Movie ID {movie_id} does not exist"}), 404

        cursor.execute("""
            INSERT INTO user_interactions (
                user_id, movie_id, interaction_type, watch_duration, completion_pct,
                recommendation_source, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], movie_id, interaction_type, watch_duration, completion_pct, source, session_id))
        conn.commit()
        return jsonify({"status": "recorded", "type": interaction_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# 5. WATCH HISTORY & CONTINUE WATCHING
# ============================================================

@app.route("/api/watch-progress", methods=["POST"])
@login_required
def update_watch_progress(user):
    """
    Updates live playback progress percentage for Continue Watching row.
    Marks movie as completed if progress >= 90%.
    """
    data = request.get_json() or {}
    movie_id = data.get("movie_id")
    progress_pct = float(data.get("progress_pct", 0.0))

    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    completed = 1 if progress_pct >= 90.0 else 0

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM movies WHERE id = ?", (movie_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Movie ID {movie_id} does not exist"}), 404

        cursor.execute("""
            INSERT INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                progress_pct = excluded.progress_pct,
                completed = excluded.completed,
                last_watched_at = CURRENT_TIMESTAMP
        """, (user["id"], movie_id, progress_pct, completed))

        # Also log an interaction milestone
        cursor.execute("""
            INSERT INTO user_interactions (user_id, movie_id, interaction_type, completion_pct)
            VALUES (?, ?, 'watch_progress', ?)
        """, (user["id"], movie_id, progress_pct))

        conn.commit()
        return jsonify({"status": "progress updated", "progress_pct": progress_pct, "completed": bool(completed)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/watch-history", methods=["GET"])
@login_required
def get_watch_history(user):
    """Chronological viewing history showing completed and in-progress movies."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT wh.progress_pct, wh.completed, wh.last_watched_at,
               m.id, m.title, m.release_year, m.poster_url, m.backdrop_url, m.duration,
               GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM watch_history wh
        JOIN movies m ON wh.movie_id = m.id
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE wh.user_id = ?
        GROUP BY m.id
        ORDER BY wh.last_watched_at DESC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        d = dict(r)
        d["genres"] = [g.strip() for g in (d.get("genres_list") or "").split(",") if g.strip()]
        history.append(d)
    return jsonify(history)


# ============================================================
# 6. WATCHLIST
# ============================================================

@app.route("/api/watchlist", methods=["GET"])
@login_required
def get_watchlist(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT wl.added_at, m.id, m.title, m.release_year, m.average_rating,
               m.poster_url, m.backdrop_url, m.duration, m.overview,
               GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM watchlist wl
        JOIN movies m ON wl.movie_id = m.id
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE wl.user_id = ?
        GROUP BY m.id
        ORDER BY wl.added_at DESC
    """, (user["id"],))
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        d = dict(r)
        d["genres"] = [g.strip() for g in (d.get("genres_list") or "").split(",") if g.strip()]
        d["in_watchlist"] = True
        items.append(d)
    return jsonify(items)


@app.route("/api/watchlist/toggle", methods=["POST"])
@login_required
def toggle_watchlist(user):
    data = request.get_json() or {}
    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify({"error": "movie_id is required"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM movies WHERE id = ?", (movie_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"Movie ID {movie_id} does not exist"}), 404

        cursor.execute("SELECT id FROM watchlist WHERE user_id = ? AND movie_id = ?", (user["id"], movie_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user["id"], movie_id))
            in_watchlist = False
        else:
            cursor.execute("INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)", (user["id"], movie_id))
            cursor.execute("""
                INSERT INTO user_interactions (user_id, movie_id, interaction_type)
                VALUES (?, ?, 'watchlist_add')
            """, (user["id"], movie_id))
            in_watchlist = True

        conn.commit()
        return jsonify({"movie_id": movie_id, "in_watchlist": in_watchlist})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# 7. SOCIAL RECOMMENDATIONS & FRIENDS
# ============================================================

@app.route("/api/friends", methods=["GET"])
@login_required
def get_friends(user):
    """Returns user's accepted friends and recent friend movie activity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username, u.email, f.created_at,
               (
                   SELECT m.title FROM watch_history wh
                   JOIN movies m ON wh.movie_id = m.id
                   WHERE wh.user_id = u.id AND wh.progress_pct >= 50
                   ORDER BY wh.last_watched_at DESC LIMIT 1
               ) AS last_watched_movie
        FROM friends f
        JOIN users u ON f.friend_user_id = u.id
        WHERE f.user_id = ?
    """, (user["id"],))
    friends = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(friends)


@app.route("/api/friends/search", methods=["GET"])
@login_required
def search_friends(user):
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.username,
               CASE
                   WHEN f.id IS NOT NULL THEN 'friends'
                   WHEN fr.id IS NOT NULL THEN 'pending'
                   ELSE 'none'
               END AS connection_status
        FROM users u
        LEFT JOIN friends f ON (f.user_id = ? AND f.friend_user_id = u.id)
        LEFT JOIN friend_requests fr ON (fr.sender_id = ? AND fr.receiver_id = u.id AND fr.status = 'pending')
        WHERE u.id != ? AND (LOWER(u.username) LIKE LOWER(?) OR LOWER(u.email) LIKE LOWER(?))
        LIMIT 10
    """, (user["id"], user["id"], user["id"], f"%{query}%", f"%{query}%"))
    results = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(results)


@app.route("/api/friends/request", methods=["POST"])
@login_required
def send_friend_request(user):
    data = request.get_json() or {}
    target_id = data.get("target_user_id")

    if not target_id or target_id == user["id"]:
        return jsonify({"error": "Invalid target user"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if already friends
        cursor.execute("SELECT id FROM friends WHERE user_id = ? AND friend_user_id = ?", (user["id"], target_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({"message": "Already friends"}), 200

        # Auto-accept for smooth demo experience
        cursor.execute("INSERT OR IGNORE INTO friends (user_id, friend_user_id) VALUES (?, ?)", (user["id"], target_id))
        cursor.execute("INSERT OR IGNORE INTO friends (user_id, friend_user_id) VALUES (?, ?)", (target_id, user["id"]))
        conn.commit()
        conn.close()
        return jsonify({"message": "Friend connected successfully", "status": "friends"})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


# ============================================================
# 8. SEARCH & DISCOVERY
# ============================================================

@app.route("/api/search", methods=["GET"])
def search_movies():
    query = request.args.get("q", "").strip()
    genre_filter = request.args.get("genre", "").strip()
    sort_by = request.args.get("sort", "popularity") # 'popularity', 'rating', 'year'

    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if query:
        conditions.append("""(
            LOWER(m.title) LIKE LOWER(?) OR
            LOWER(m.director) LIKE LOWER(?) OR
            LOWER(m.cast_members) LIKE LOWER(?) OR
            LOWER(m.tags) LIKE LOWER(?)
        )""")
        q_wild = f"%{query}%"
        params.extend([q_wild, q_wild, q_wild, q_wild])

    if genre_filter and genre_filter.lower() != "all":
        conditions.append("""m.id IN (
            SELECT mg.movie_id FROM movie_genres mg
            JOIN genres g ON mg.genre_id = g.id
            WHERE LOWER(g.name) = LOWER(?)
        )""")
        params.append(genre_filter)

    order_clause = "m.rating_count DESC, m.average_rating DESC"
    if sort_by == "rating":
        order_clause = "m.average_rating DESC, m.rating_count DESC"
    elif sort_by == "year":
        order_clause = "m.release_year DESC, m.rating_count DESC"

    where_str = " AND ".join(conditions)
    cursor.execute(f"""
        SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE {where_str}
        GROUP BY m.id
        ORDER BY {order_clause}
        LIMIT 40
    """, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["genres"] = [g.strip() for g in (d.get("genres_list") or "").split(",") if g.strip()]
        d["match_percentage"] = int(min(99, max(75, round((d["average_rating"] or 3.5) * 19))))
        results.append(d)
    return jsonify(results)


# ============================================================
# 9. ADMIN PANEL & MOVIE MANAGEMENT
# ============================================================

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats(user):
    """Platform statistics and analytical metrics for administrators."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS count FROM movies")
    total_movies = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM users")
    total_users = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM ratings")
    total_ratings = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM user_interactions")
    total_interactions = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT g.name, COUNT(mg.movie_id) AS movie_count
        FROM genres g
        JOIN movie_genres mg ON g.id = mg.genre_id
        GROUP BY g.id
        ORDER BY movie_count DESC
        LIMIT 8
    """)
    top_genres = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({
        "total_movies": total_movies,
        "total_users": total_users,
        "total_ratings": total_ratings,
        "total_interactions": total_interactions,
        "top_genres": top_genres
    })


@app.route("/api/admin/movies", methods=["GET"])
@admin_required
def admin_list_movies(user):
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page
    search = request.args.get("search", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE LOWER(m.title) LIKE LOWER(?)
            GROUP BY m.id
            ORDER BY m.id DESC
            LIMIT ? OFFSET ?
        """, (f"%{search}%", per_page, offset))
    else:
        cursor.execute("""
            SELECT m.*, GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            GROUP BY m.id
            ORDER BY m.id DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))

    rows = cursor.fetchall()
    conn.close()

    movies = []
    for r in rows:
        d = dict(r)
        d["genres"] = [g.strip() for g in (d.get("genres_list") or "").split(",") if g.strip()]
        movies.append(d)
    return jsonify(movies)


@app.route("/api/admin/movies", methods=["POST"])
@admin_required
def admin_create_movie(user):
    """
    Creates a new movie in the database with validation,
    genre mapping, and instant recommendation eligibility.
    """
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    release_year = int(data.get("release_year", 2024))
    duration = int(data.get("duration", 115))
    overview = data.get("overview", "").strip()
    poster_url = data.get("poster_url", "").strip()
    backdrop_url = data.get("backdrop_url", "").strip()
    director = data.get("director", "").strip()
    cast_members = data.get("cast_members", "").strip()
    genres = data.get("genres", []) # list of genre names or comma separated
    tags = data.get("tags", "").strip()
    rating = float(data.get("rating", 4.0))

    if not title:
        return jsonify({"error": "Movie title is required"}), 400

    if not poster_url:
        poster_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80"
    if not backdrop_url:
        backdrop_url = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&q=80"

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO movies (
                title, release_year, duration, overview, poster_url, backdrop_url,
                director, cast_members, average_rating, rating_count, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (title, release_year, duration, overview, poster_url, backdrop_url, director, cast_members, rating, tags))
        movie_id = cursor.lastrowid

        # Handle genres
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]

        for g_name in genres:
            cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g_name.strip(),))
            cursor.execute("SELECT id FROM genres WHERE name = ?", (g_name.strip(),))
            g_id = cursor.fetchone()["id"]
            cursor.execute("INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)", (movie_id, g_id))

        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    # Invalidate / refit recommendation cache
    engine.content_model.fit()

    return jsonify({"message": "Movie added successfully", "movie_id": movie_id}), 201


@app.route("/api/admin/movies/<int:movie_id>", methods=["DELETE"])
@admin_required
def admin_delete_movie(user, movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Movie deleted successfully", "movie_id": movie_id})


# ============================================================
# 10. SERVE STATIC ASSETS & INDEX
# ============================================================

@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join("static", path)):
        return send_from_directory("static", path)
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Movie Recommendation Platform server at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
