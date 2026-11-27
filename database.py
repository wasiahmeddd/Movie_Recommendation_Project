"""
Database module for the Movie Recommendation Platform.
Implements SQLite schema, connection management, and helper functions.
Supports Users, Roles, Preferences, Movies, Genres, Ratings, Interactions,
Watch History, Watchlist, Friends, and Social Sharing.
"""

import sqlite3
import os
import hashlib
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def hash_password(password: str, salt: str = "movienetflix_salt_2026") -> str:
    """Secure password hashing using SHA-256 with salt."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_db():
    """Creates all required tables, constraints, and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user', -- 'user' or 'admin'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. User Preferences (Onboarding Genres)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        genre TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (user_id, genre)
    )
    """)

    # 3. Movies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movielens_id INTEGER UNIQUE,
        tmdb_id INTEGER,
        title TEXT NOT NULL,
        release_year INTEGER,
        duration INTEGER DEFAULT 110, -- duration in minutes
        overview TEXT,
        poster_url TEXT,
        backdrop_url TEXT,
        director TEXT,
        cast_members TEXT,
        average_rating REAL DEFAULT 0.0,
        rating_count INTEGER DEFAULT 0,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Genres Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    """)

    # 5. Movie Genres (Many-to-Many Relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movie_genres (
        movie_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        PRIMARY KEY (movie_id, genre_id),
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
        FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
    )
    """)

    # 6. Ratings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
        timestamp INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
        UNIQUE (user_id, movie_id)
    )
    """)

    # 7. User Interactions Tracking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        interaction_type TEXT NOT NULL, 
        -- 'click', 'view_details', 'watchlist_add', 'watch_start', 'watch_progress', 'complete', 'like', 'dislike', 'skip', 'impression'
        watch_duration INTEGER DEFAULT 0, -- seconds watched
        completion_pct REAL DEFAULT 0.0,
        recommendation_source TEXT,
        session_id TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
    )
    """)

    # 8. Watch History & Continue Watching
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        progress_pct REAL DEFAULT 0.0,
        completed INTEGER DEFAULT 0, -- 1 if >= 90% watched
        last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
        UNIQUE (user_id, movie_id)
    )
    """)

    # 9. Watchlist Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
        UNIQUE (user_id, movie_id)
    )
    """)

    # 10. Friends Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (friend_user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (user_id, friend_user_id)
    )
    """)

    # 11. Friend Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (sender_id, receiver_id)
    )
    """)

    # 12. User Privacy Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_privacy_settings (
        user_id INTEGER PRIMARY KEY,
        share_activity_with_friends INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(average_rating)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings(movie_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_user ON user_interactions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_movie ON user_interactions(movie_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_watch_history_user ON watch_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id)")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
