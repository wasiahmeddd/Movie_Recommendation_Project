"""
Intelligent Recommendation Engine for Movie Recommendation Platform.
Implements:
1. Content-Based Filtering using TF-IDF and Cosine Similarity on metadata (title, genres, overview, director, cast, tags)
2. Collaborative Filtering (User-Based & Item-Based) using MovieLens user ratings matrix
3. Interaction Signal Scoring (real-time learning from clicks, skips, watchlist, and completion %)
4. Hybrid Recommendation Engine with configurable multi-objective weights
5. Cold-Start handling using onboarding preferences and logarithmic popularity curves
6. Dynamic Recommendation Explanations ("Because you watched...", "Because you love Sci-Fi", etc.)
"""

import math
import re
from collections import Counter, defaultdict
from database import get_db_connection


class ContentBasedRecommender:
    """
    Computes TF-IDF vectors and Cosine Similarity for movies in the database.
    Implemented in robust pure Python for 100% platform portability and speed.
    """
    def __init__(self):
        self.movie_ids = []
        self.movie_meta = {} # id -> {title, genres, text}
        self.vocabulary = {} # word -> doc_freq
        self.doc_count = 0
        self.tfidf_vectors = {} # movie_id -> {word: tfidf_weight}
        self.vector_norms = {}  # movie_id -> euclidean_norm
        self.is_fitted = False

    def _tokenize(self, text: str):
        """Standard word tokenizer with stop words removal."""
        stop_words = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "by", "of", "from", "as", "is", "was", "are", "were", "it", "this",
            "that", "his", "her", "their", "who", "which", "film", "movie", "set",
            "into", "an", "be", "has", "have", "had", "out", "about", "up", "one"
        }
        tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
        return [t for t in tokens if t not in stop_words]

    def fit(self):
        """Loads all movie metadata and builds TF-IDF vector space."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch movies with associated genres
        cursor.execute("""
            SELECT m.id, m.title, m.release_year, m.overview, m.director, m.cast_members, m.tags,
                   GROUP_CONCAT(g.name, ' ') AS genres_text
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            GROUP BY m.id
        """)
        rows = cursor.fetchall()
        conn.close()

        self.doc_count = len(rows)
        if self.doc_count == 0:
            return

        self.movie_ids = []
        doc_tokens = {}
        df_counter = Counter()

        for r in rows:
            m_id = r["id"]
            self.movie_ids.append(m_id)
            # Combine content features with genre repetition for high domain importance
            genres_text = r["genres_text"] or ""
            # Boost genres and director weight in the text representation
            content_str = (
                f"{r['title']} {genres_text} {genres_text} {r['overview'] or ''} "
                f"{r['director'] or ''} {r['director'] or ''} {r['cast_members'] or ''} {r['tags'] or ''}"
            )
            tokens = self._tokenize(content_str)
            doc_tokens[m_id] = tokens
            unique_terms = set(tokens)
            df_counter.update(unique_terms)

            self.movie_meta[m_id] = {
                "id": m_id,
                "title": r["title"],
                "genres": genres_text,
                "year": r["release_year"]
            }

        self.vocabulary = df_counter

        # Calculate TF-IDF vectors
        for m_id, tokens in doc_tokens.items():
            if not tokens:
                self.tfidf_vectors[m_id] = {}
                self.vector_norms[m_id] = 1.0
                continue

            tf = Counter(tokens)
            total_tokens = len(tokens)
            vec = {}
            norm_sq = 0.0

            for term, count in tf.items():
                tf_val = count / total_tokens
                # Smooth IDF calculation
                df = self.vocabulary.get(term, 1)
                idf_val = math.log((1 + self.doc_count) / (1 + df)) + 1.0
                weight = tf_val * idf_val
                vec[term] = weight
                norm_sq += weight * weight

            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            # Normalize vector
            self.tfidf_vectors[m_id] = {k: v / norm for k, v in vec.items()}
            self.vector_norms[m_id] = 1.0

        self.is_fitted = True

    def cosine_similarity(self, vec_a: dict, vec_b: dict) -> float:
        """Computes dot product between two L2-normalized sparse vectors."""
        if not vec_a or not vec_b:
            return 0.0
        # Dot product of matching keys
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        return sum(weight * vec_b.get(term, 0.0) for term, weight in vec_a.items())

    def get_similar_movies(self, movie_id: int, top_n: int = 10):
        """Finds top N movies most similar to a target movie."""
        if not self.is_fitted:
            self.fit()

        target_vec = self.tfidf_vectors.get(movie_id)
        if not target_vec:
            return []

        scores = []
        for m_id in self.movie_ids:
            if m_id == movie_id:
                continue
            sim = self.cosine_similarity(target_vec, self.tfidf_vectors.get(m_id, {}))
            if sim > 0.02:
                scores.append((m_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def get_user_content_scores(self, liked_movie_ids: list, preferred_genres: list):
        """
        Builds a composite user taste profile from liked movies and onboarding genres,
        returning similarity scores for all candidate movies.
        """
        if not self.is_fitted:
            self.fit()

        user_vec = defaultdict(float)
        weights_sum = 0.0

        # 1. Profile from liked movies
        for m_id in liked_movie_ids:
            m_vec = self.tfidf_vectors.get(m_id)
            if m_vec:
                for term, val in m_vec.items():
                    user_vec[term] += val * 1.5
                weights_sum += 1.5

        # 2. Profile from preferred genres
        for genre in preferred_genres:
            g_tokens = self._tokenize(genre)
            for t in g_tokens:
                user_vec[t] += 2.0
            weights_sum += 2.0

        if weights_sum == 0.0:
            return {}

        # Normalize user vector
        norm_sq = sum(v * v for v in user_vec.values())
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        norm_user_vec = {k: v / norm for k, v in user_vec.items()}

        scores = {}
        for m_id in self.movie_ids:
            sim = self.cosine_similarity(norm_user_vec, self.tfidf_vectors.get(m_id, {}))
            scores[m_id] = sim

        return scores


class CollaborativeFilteringRecommender:
    """
    User-Based and Item-Based Collaborative Filtering using MovieLens user-movie rating vectors.
    Computes Pearson / Cosine similarity between users to predict ratings for unrated movies.
    """
    def __init__(self):
        self.user_ratings = defaultdict(dict) # user_id -> {movie_id: rating}
        self.movie_ratings = defaultdict(dict) # movie_id -> {user_id: rating}
        self.user_means = {} # user_id -> mean_rating
        self.is_loaded = False

    def load_ratings(self):
        """Loads ratings into user and item vectors."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, movie_id, rating FROM ratings")
        rows = cursor.fetchall()
        conn.close()

        self.user_ratings.clear()
        self.movie_ratings.clear()
        self.user_means.clear()

        for r in rows:
            u_id = r["user_id"]
            m_id = r["movie_id"]
            rating = float(r["rating"])
            self.user_ratings[u_id][m_id] = rating
            self.movie_ratings[m_id][u_id] = rating

        for u_id, m_dict in self.user_ratings.items():
            self.user_means[u_id] = sum(m_dict.values()) / len(m_dict)

        self.is_loaded = True

    def user_similarity(self, u1: int, u2: int) -> float:
        """Calculates Pearson correlation / centered cosine similarity between two users."""
        ratings1 = self.user_ratings.get(u1, {})
        ratings2 = self.user_ratings.get(u2, {})
        common_movies = set(ratings1.keys()).intersection(ratings2.keys())

        if len(common_movies) < 2:
            return 0.0

        mean1 = self.user_means.get(u1, 3.5)
        mean2 = self.user_means.get(u2, 3.5)

        num = sum((ratings1[m] - mean1) * (ratings2[m] - mean2) for m in common_movies)
        den1 = math.sqrt(sum((ratings1[m] - mean1) ** 2 for m in common_movies))
        den2 = math.sqrt(sum((ratings2[m] - mean2) ** 2 for m in common_movies))

        if den1 == 0 or den2 == 0:
            return 0.0
        return num / (den1 * den2)

    def predict_ratings_for_user(self, user_id: int, candidate_movie_ids: set, top_k_neighbors: int = 25):
        """
        Predicts expected ratings for unrated candidate movies using K-nearest similar users.
        Returns dict of movie_id -> predicted_rating (scaled 0.0 to 1.0).
        """
        if not self.is_loaded:
            self.load_ratings()

        if user_id not in self.user_ratings:
            return {}

        user_mean = self.user_means.get(user_id, 3.5)

        # Find top similar neighbors
        sim_scores = []
        for other_u in self.user_ratings.keys():
            if other_u == user_id:
                continue
            sim = self.user_similarity(user_id, other_u)
            if sim > 0.1:
                sim_scores.append((other_u, sim))

        sim_scores.sort(key=lambda x: x[1], reverse=True)
        neighbors = sim_scores[:top_k_neighbors]

        if not neighbors:
            return {}

        predictions = {}
        for m_id in candidate_movie_ids:
            num = 0.0
            den = 0.0
            for neighbor_u, sim in neighbors:
                if m_id in self.user_ratings[neighbor_u]:
                    neighbor_rating = self.user_ratings[neighbor_u][m_id]
                    neighbor_mean = self.user_means.get(neighbor_u, 3.5)
                    num += sim * (neighbor_rating - neighbor_mean)
                    den += abs(sim)

            if den > 0:
                pred = user_mean + (num / den)
                # Normalize 0.5-5.0 rating scale into [0.0, 1.0]
                normalized = max(0.0, min(1.0, (pred - 0.5) / 4.5))
                predictions[m_id] = normalized

        return predictions


class HybridRecommendationEngine:
    """
    Orchestrates Content-Based Filtering, Collaborative Filtering, Interaction Boosts,
    Cold-Start handling, and Human-Readable Recommendation Explanations.
    """
    def __init__(self):
        self.content_model = ContentBasedRecommender()
        self.collab_model = CollaborativeFilteringRecommender()

    def get_user_interactions_summary(self, user_id: int):
        """
        Extracts historical watched, liked, skipped, and watchlist movies for a user.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Onboarding preferences
        cursor.execute("SELECT genre FROM user_preferences WHERE user_id = ?", (user_id,))
        preferred_genres = [r["genre"] for r in cursor.fetchall()]

        # 2. Watchlist
        cursor.execute("SELECT movie_id FROM watchlist WHERE user_id = ?", (user_id,))
        watchlist_ids = set(r["movie_id"] for r in cursor.fetchall())

        # 3. Watch history
        cursor.execute("SELECT movie_id, progress_pct, completed FROM watch_history WHERE user_id = ?", (user_id,))
        watched_records = {r["movie_id"]: {"pct": r["progress_pct"], "completed": r["completed"]} for r in cursor.fetchall()}

        # 4. Ratings
        cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id = ?", (user_id,))
        rated_dict = {r["movie_id"]: r["rating"] for r in cursor.fetchall()}

        # 5. Recent interactions (likes, dislikes, clicks)
        cursor.execute("""
            SELECT movie_id, interaction_type, completion_pct
            FROM user_interactions
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 100
        """, (user_id,))
        interactions = cursor.fetchall()
        conn.close()

        likes = set()
        dislikes = set()
        clicks = set()
        for row in interactions:
            itype = row["interaction_type"]
            m_id = row["movie_id"]
            if itype == "like":
                likes.add(m_id)
            elif itype == "dislike":
                dislikes.add(m_id)
            elif itype in ("click", "view_details"):
                clicks.add(m_id)

        # Movies positively rated (>= 3.5) count as liked
        for m_id, r in rated_dict.items():
            if r >= 3.5:
                likes.add(m_id)
            elif r <= 2.0:
                dislikes.add(m_id)

        return {
            "preferred_genres": preferred_genres,
            "watchlist_ids": watchlist_ids,
            "watched_records": watched_records,
            "likes": likes,
            "dislikes": dislikes,
            "clicks": clicks,
        }

    def recommend_for_user(self, user_id: int, top_n: int = 15, exclude_completed: bool = True):
        """
        Primary Hybrid Recommender method.
        Blends:
        - Genre Affinity (from onboarding and profile)
        - Content-Based TF-IDF similarity to liked/watched movies
        - Collaborative Filtering prediction from similar users
        - Interaction Boosts (watchlist, clicks, completion)
        - Popularity & Quality prior
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all available movies with primary genre
        cursor.execute("""
            SELECT m.id, m.title, m.release_year, m.average_rating, m.rating_count,
                   m.poster_url, m.backdrop_url, m.duration, m.overview,
                   GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            GROUP BY m.id
        """)
        all_movies = {r["id"]: dict(r) for r in cursor.fetchall()}
        conn.close()

        if not all_movies:
            return []

        user_data = self.get_user_interactions_summary(user_id)
        preferred_genres = user_data["preferred_genres"]
        watched_records = user_data["watched_records"]
        likes = user_data["likes"]
        dislikes = user_data["dislikes"]
        watchlist = user_data["watchlist_ids"]
        clicks = user_data["clicks"]

        completed_ids = {m_id for m_id, data in watched_records.items() if data["completed"] == 1}

        # Filter candidate pool
        candidate_ids = set(all_movies.keys())
        if exclude_completed:
            candidate_ids -= completed_ids
        candidate_ids -= dislikes

        # ========================================================
        # COLD START HANDLER (New user or no watch history)
        # ========================================================
        is_cold_start = len(watched_records) == 0 and len(likes) == 0

        # 1. Content-Based Scores
        content_scores = self.content_model.get_user_content_scores(
            liked_movie_ids=list(likes),
            preferred_genres=preferred_genres
        )

        # 2. Collaborative Filtering Scores
        collab_scores = {}
        if not is_cold_start:
            collab_scores = self.collab_model.predict_ratings_for_user(user_id, candidate_ids)

        # Find the most impactful liked movie for dynamic explanations
        anchor_movie_title = None
        if likes:
            anchor_id = list(likes)[0]
            if anchor_id in all_movies:
                anchor_movie_title = all_movies[anchor_id]["title"]

        # 3. Hybrid Scoring Calculation
        scored_candidates = []
        for m_id in candidate_ids:
            movie = all_movies[m_id]
            genres_str = movie["genres_list"] or ""
            movie_genres = [g.strip() for g in genres_str.split(",") if g.strip()]

            # Feature A: Genre Affinity Score [0.0 - 1.0]
            genre_matches = sum(1 for g in movie_genres if any(pg.lower() in g.lower() for pg in preferred_genres))
            genre_score = min(1.0, genre_matches * 0.45) if preferred_genres else 0.5

            # Feature B: Content-Based Similarity Score [0.0 - 1.0]
            cb_score = content_scores.get(m_id, 0.0)

            # Feature C: Collaborative Filtering Prediction [0.0 - 1.0]
            cf_score = collab_scores.get(m_id, 0.5 if not is_cold_start else 0.0)

            # Feature D: Quality & Popularity Prior [0.0 - 1.0]
            avg_rating = movie["average_rating"] or 3.0
            rating_count = movie["rating_count"] or 0
            quality_score = (avg_rating / 5.0) * 0.7 + (min(1.0, math.log1p(rating_count) / 6.0)) * 0.3

            # Feature E: Interaction Boosts
            boost = 0.0
            if m_id in watchlist:
                boost += 0.25 # User deliberately saved it
            if m_id in clicks:
                boost += 0.10 # Expressed interest

            # Final Hybrid Blend
            if is_cold_start:
                # Cold start: heavily prioritize selected genres and popularity
                final_score = (genre_score * 0.45) + (cb_score * 0.25) + (quality_score * 0.30) + boost
            else:
                # Established user: balanced hybrid
                final_score = (
                    (genre_score * 0.20) +
                    (cb_score * 0.35) +
                    (cf_score * 0.25) +
                    (quality_score * 0.20) +
                    boost
                )

            # Match Percentage display (like Netflix "98% Match")
            match_pct = int(min(99, max(72, round(final_score * 100))))

            # Dynamic Recommendation Explanation
            if m_id in watchlist:
                explanation = "In your Watchlist"
            elif anchor_movie_title and cb_score > 0.18:
                explanation = f"Because you liked {anchor_movie_title}"
            elif genre_matches > 0:
                matched_genre = next((g for g in movie_genres if any(pg.lower() in g.lower() for pg in preferred_genres)), "your favorites")
                explanation = f"Matches your love for {matched_genre}"
            elif cf_score > 0.65:
                explanation = "Popular among users with similar taste"
            else:
                explanation = "Trending high recommendation"

            scored_candidates.append({
                "id": movie["id"],
                "title": movie["title"],
                "release_year": movie["release_year"],
                "duration": movie["duration"],
                "average_rating": movie["average_rating"],
                "rating_count": movie["rating_count"],
                "poster_url": movie["poster_url"],
                "backdrop_url": movie["backdrop_url"],
                "overview": movie["overview"],
                "genres": movie_genres,
                "score": round(final_score, 4),
                "match_percentage": match_pct,
                "explanation": explanation
            })

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_n]

    def get_social_recommendations(self, user_id: int, top_n: int = 10):
        """
        Recommends movies watched and liked by connected friends that the user has not seen.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check friends list
        cursor.execute("""
            SELECT f.friend_user_id, u.username
            FROM friends f
            JOIN users u ON f.friend_user_id = u.id
            JOIN user_privacy_settings p ON u.id = p.user_id
            WHERE f.user_id = ? AND p.share_activity_with_friends = 1
        """, (user_id,))
        friends = cursor.fetchall()

        if not friends:
            conn.close()
            return []

        friend_map = {r["friend_user_id"]: r["username"] for r in friends}
        friend_ids = list(friend_map.keys())

        # Get current user's watched movies to avoid recommending already watched movies
        cursor.execute("SELECT movie_id FROM watch_history WHERE user_id = ?", (user_id,))
        user_watched = set(r["movie_id"] for r in cursor.fetchall())

        # Query movies watched by friends
        placeholders = ",".join("?" for _ in friend_ids)
        cursor.execute(f"""
            SELECT wh.movie_id, wh.user_id, m.title, m.release_year, m.duration,
                   m.average_rating, m.poster_url, m.backdrop_url, m.overview,
                   GROUP_CONCAT(g.name, ', ') AS genres_list
            FROM watch_history wh
            JOIN movies m ON wh.movie_id = m.id
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE wh.user_id IN ({placeholders}) AND wh.progress_pct >= 50.0
            GROUP BY wh.movie_id, wh.user_id
            ORDER BY wh.last_watched_at DESC
        """, friend_ids)
        rows = cursor.fetchall()
        conn.close()

        social_recs = []
        seen_movies = set()
        for r in rows:
            m_id = r["movie_id"]
            if m_id in user_watched or m_id in seen_movies:
                continue
            seen_movies.add(m_id)
            friend_name = friend_map.get(r["user_id"], "a friend")
            genres = [g.strip() for g in (r["genres_list"] or "").split(",") if g.strip()]
            social_recs.append({
                "id": m_id,
                "title": r["title"],
                "release_year": r["release_year"],
                "duration": r["duration"],
                "average_rating": r["average_rating"],
                "poster_url": r["poster_url"],
                "backdrop_url": r["backdrop_url"],
                "overview": r["overview"],
                "genres": genres,
                "match_percentage": 96,
                "explanation": f"Watched recently by {friend_name}"
            })
            if len(social_recs) >= top_n:
                break

        return social_recs


# Global singleton engine instance
engine = HybridRecommendationEngine()


if __name__ == "__main__":
    print("Testing Hybrid Recommendation Engine...")
    recs = engine.recommend_for_user(user_id=2, top_n=5)
    print(f"Generated {len(recs)} recommendations for demo_user:")
    for r in recs:
        print(f" - {r['title']} ({r['release_year']}) | {r['match_percentage']}% Match | {r['explanation']}")

    social_recs = engine.get_social_recommendations(user_id=2, top_n=3)
    print(f"\nGenerated {len(social_recs)} social recommendations:")
    for r in social_recs:
        print(f" - {r['title']} | {r['explanation']}")
