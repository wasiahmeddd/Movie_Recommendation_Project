"""
PROJECT 12: MOVIE & CONTENT RECOMMENDATION INTELLIGENCE SYSTEM
Beginner-friendly end-to-end prototype following an 8-step workflow.

Run:
    python main.py

This first version uses a small, reproducible sample dataset.
Replace create_sample_data() with MovieLens loading when ready.
"""

# ============================================================
# STEP 0: IMPORT LIBRARIES
# ============================================================
import os
import math

try:
    import numpy as np
    import pandas as pd
except Exception as e:
    np = None
    pd = None

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTS_AVAILABLE = True
except Exception:
    plt = None
    sns = None
    PLOTS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

RANDOM_STATE = 42
OUTPUT_DIR = os.path.join("outputs", "graphs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# STEP 1: PROBLEM UNDERSTANDING
# ============================================================
"""
Problem:
Users find it difficult to discover movies they may enjoy.

Goal:
Use movie genres/descriptions and user ratings to recommend movies.

This prototype demonstrates:
1. Popularity-based recommendations.
2. Content-based recommendations using TF-IDF + cosine similarity.
3. A simple rating-prediction experiment using Linear Regression.

Cold start:
- New user: show popular movies until preferences are known.
- New movie: content-based recommendations can use its metadata.
"""


# ============================================================
# STEP 2: DATA COLLECTION
# ============================================================
def create_sample_data():
    """Create small movie and rating tables for a first demo."""
    movies = pd.DataFrame([
        [1, "Interstellar", "Sci-Fi Adventure", "Space travel and a mission to save humanity", 2014],
        [2, "The Martian", "Sci-Fi Adventure", "An astronaut survives alone on Mars", 2015],
        [3, "Gravity", "Sci-Fi Thriller", "Astronauts struggle to survive in space", 2013],
        [4, "Arrival", "Sci-Fi Drama", "A linguist communicates with visitors from space", 2016],
        [5, "Titanic", "Romance Drama", "A romance unfolds aboard a famous ship", 1997],
        [6, "The Notebook", "Romance Drama", "Two people experience a lasting love story", 2004],
        [7, "La La Land", "Romance Musical", "A musician and an actor pursue their dreams", 2016],
        [8, "The Dark Knight", "Action Crime", "A hero faces a criminal mastermind", 2008],
        [9, "Inception", "Sci-Fi Action", "A team enters dreams to complete a mission", 2010],
        [10, "The Avengers", "Action Adventure", "Heroes unite to protect the world", 2012],
        [11, "Finding Nemo", "Animation Adventure", "A father searches the ocean for his son", 2003],
        [12, "Toy Story", "Animation Comedy", "Toys come alive when people are away", 1995],
        [13, "Coco", "Animation Drama", "A boy explores family and music", 2017],
        [14, "Joker", "Drama Crime", "A troubled comedian experiences a difficult city life", 2019],
        [15, "The Shawshank Redemption", "Drama", "Friendship and hope inside a prison", 1994],
    ], columns=["movieId", "title", "genres", "overview", "release_year"])

    ratings_rows = [
        [101, 1, 5], [101, 2, 5], [101, 3, 4], [101, 4, 4], [101, 9, 5],
        [102, 5, 5], [102, 6, 5], [102, 7, 4], [102, 13, 3],
        [103, 8, 5], [103, 9, 4], [103, 10, 5], [103, 14, 4],
        [104, 11, 5], [104, 12, 5], [104, 13, 5], [104, 7, 3],
        [105, 1, 4], [105, 4, 5], [105, 9, 4], [105, 2, 4],
        [106, 5, 4], [106, 6, 4], [106, 7, 5], [106, 15, 4],
        [107, 8, 4], [107, 10, 4], [107, 14, 5], [107, 15, 3],
        [108, 11, 4], [108, 12, 5], [108, 13, 4], [108, 5, 3],
        [109, 1, 5], [109, 2, 4], [109, 8, 3], [109, 9, 5],
        [110, 5, 5], [110, 7, 4], [110, 6, 5], [110, 14, 3],
        [111, 8, 5], [111, 10, 4], [111, 9, 4], [111, 3, 3],
        [112, 11, 5], [112, 13, 4], [112, 12, 4], [112, 15, 4],
    ]
    ratings = pd.DataFrame(ratings_rows, columns=["userId", "movieId", "rating"])
    return movies, ratings


# ============================================================
# STEP 3: DATA PREPARATION
# ============================================================
def clean_data(movies, ratings):
    """Clean tables, validate ratings, engineer text features."""
    movies = movies.copy()
    ratings = ratings.copy()

    # Remove duplicate rows.
    movies = movies.drop_duplicates(subset=["movieId"])
    ratings = ratings.drop_duplicates(subset=["userId", "movieId"])

    # Fill missing movie metadata.
    for column in ["title", "genres", "overview"]:
        movies[column] = movies[column].fillna("Unknown")

    # Fix data types.
    movies["movieId"] = pd.to_numeric(movies["movieId"], errors="coerce")
    ratings["movieId"] = pd.to_numeric(ratings["movieId"], errors="coerce")
    ratings["userId"] = pd.to_numeric(ratings["userId"], errors="coerce")
    ratings["rating"] = pd.to_numeric(ratings["rating"], errors="coerce")

    movies = movies.dropna(subset=["movieId"])
    ratings = ratings.dropna(subset=["userId", "movieId", "rating"])

    # Keep only valid ratings (MovieLens commonly uses a 0.5-5 scale).
    ratings = ratings[ratings["rating"].between(0.5, 5.0)]

    # Standardize genre text and combine metadata for content modelling.
    movies["genres"] = movies["genres"].str.replace("|", " ", regex=False).str.strip()
    movies["content"] = (
        movies["title"].astype(str) + " " +
        movies["genres"].astype(str) + " " +
        movies["overview"].astype(str)
    )

    # Merge tables to check that rating movie IDs have metadata.
    merged = ratings.merge(movies, on="movieId", how="inner")
    print("\nDATA CLEANING")
    print("Movies after cleaning:", len(movies))
    print("Ratings after cleaning:", len(ratings))
    print("Merged interactions:", len(merged))
    print("Missing values in movies:\n", movies.isna().sum())
    return movies, ratings, merged


# ============================================================
# STEP 4: EXPLORATORY DATA ANALYSIS (EDA)
# ============================================================
def perform_eda(movies, ratings, merged):
    print("\nEXPLORATORY DATA ANALYSIS")
    print("Number of movies:", movies["movieId"].nunique())
    print("Number of users:", ratings["userId"].nunique())
    print("Number of ratings:", len(ratings))
    print("\nRating statistics:\n", ratings["rating"].describe())

    if PLOTS_AVAILABLE:
        # 1. Rating distribution.
        plt.figure(figsize=(7, 4))
        sns.countplot(data=ratings, x="rating", color="steelblue")
        plt.title("Distribution of Movie Ratings")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "rating_distribution.png"))
        plt.close()

        # 2. Most-rated movies.
        movie_stats = ratings.groupby("movieId").agg(
            average_rating=("rating", "mean"),
            rating_count=("rating", "count")
        ).reset_index()
        popular = movie_stats.merge(movies[["movieId", "title"]], on="movieId")
        popular = popular.sort_values("rating_count", ascending=False).head(10)

        plt.figure(figsize=(9, 5))
        sns.barplot(data=popular, x="rating_count", y="title")
        plt.title("Most Rated Movies")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "most_rated_movies.png"))
        plt.close()

        # 3. Correlation heatmap for numeric movie statistics.
        plt.figure(figsize=(6, 4))
        sns.heatmap(movie_stats[["average_rating", "rating_count"]].corr(),
                    annot=True, cmap="coolwarm", vmin=-1, vmax=1)
        plt.title("Movie Statistics Correlation")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "correlation_heatmap.png"))
        plt.close()
        print("\nEDA graphs saved in:", OUTPUT_DIR)
    else:
        movie_stats = ratings.groupby("movieId").agg(
            average_rating=("rating", "mean"),
            rating_count=("rating", "count")
        ).reset_index()
        print("\nNote: matplotlib/seaborn not found. Skipping PNG chart generation.")

    # 4. Ratings by genre (a movie can have more than one genre).
    genre_rows = merged.assign(genre=merged["genres"].str.split()).explode("genre")
    genre_summary = genre_rows.groupby("genre")["rating"].mean().sort_values(ascending=False)
    print("\nAverage rating by genre:\n", genre_summary)

    print("\nEDA graphs saved in:", OUTPUT_DIR)
    return movie_stats


# ============================================================
# STEP 5: MODELING / ANALYSIS
# ============================================================
def build_content_model(movies):
    """Convert movie text to TF-IDF vectors and calculate cosine similarity."""
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(movies["content"])
    similarity_matrix = cosine_similarity(tfidf_matrix)
    return vectorizer, tfidf_matrix, similarity_matrix


def recommend_similar_movies(movie_title, movies, similarity_matrix, top_n=5):
    """Recommend movies similar to a selected movie."""
    matches = movies.index[movies["title"].str.lower() == movie_title.lower()].tolist()
    if not matches:
        print("Movie not found. Check the spelling.")
        return pd.DataFrame()

    movie_index = matches[0]
    scores = list(enumerate(similarity_matrix[movie_index]))
    scores = sorted(scores, key=lambda item: item[1], reverse=True)

    # Skip the selected movie itself.
    scores = [item for item in scores if item[0] != movie_index][:top_n]
    result = movies.iloc[[item[0] for item in scores]][
        ["movieId", "title", "genres", "release_year"]
    ].copy()
    result["similarity_score"] = [round(item[1], 3) for item in scores]
    return result


def popularity_recommendations(movies, ratings, top_n=5):
    """Recommend highly rated movies with a minimum number of ratings."""
    stats = ratings.groupby("movieId").agg(
        average_rating=("rating", "mean"),
        rating_count=("rating", "count")
    ).reset_index()

    # A small threshold for this small demo dataset.
    eligible = stats[stats["rating_count"] >= 2].copy()
    eligible["score"] = (
        eligible["average_rating"] * 0.7 +
        np.log1p(eligible["rating_count"]) * 0.3
    )
    return eligible.merge(movies, on="movieId").sort_values(
        "score", ascending=False
    )[["title", "genres", "average_rating", "rating_count", "score"]].head(top_n)


def recommend_for_user(user_id, movies, ratings, similarity_matrix, top_n=5):
    """Build a simple content profile from movies the user rated 4 or higher."""
    user_history = ratings[ratings["userId"] == user_id]
    liked_ids = user_history[user_history["rating"] >= 4]["movieId"].tolist()

    if len(user_history) == 0 or len(liked_ids) == 0:
        print("New user or no highly rated movies: showing popular recommendations.")
        return popularity_recommendations(movies, ratings, top_n)

    watched_ids = set(user_history["movieId"])
    liked_indices = movies.index[movies["movieId"].isin(liked_ids)].tolist()

    # Average similarity to the movies the user liked.
    user_scores = similarity_matrix[liked_indices].mean(axis=0)
    candidate_indices = [
        i for i, movie_id in enumerate(movies["movieId"])
        if movie_id not in watched_ids
    ]
    ranked = sorted(candidate_indices, key=lambda i: user_scores[i], reverse=True)
    result = movies.iloc[ranked[:top_n]][
        ["movieId", "title", "genres", "release_year"]
    ].copy()
    result["recommendation_score"] = [
        round(float(user_scores[i]), 3) for i in ranked[:top_n]
    ]
    return result


# ============================================================
# STEP 6: EVALUATION
# ============================================================
def precision_recall_at_k(recommended_ids, relevant_ids, k=5):
    """Calculate Precision@K and Recall@K for one user."""
    recommended = recommended_ids[:k]
    relevant = set(relevant_ids)
    if not recommended:
        return 0.0, 0.0
    hits = sum(item in relevant for item in recommended)
    precision = hits / len(recommended)
    recall = hits / len(relevant) if relevant else 0.0
    return precision, recall


def evaluate_content_model(movies, ratings, top_n=5):
    """
    Simple holdout evaluation:
    hold out one high-rated movie per eligible user, build recommendations
    from the remaining ratings, and check whether the held-out movie appears.
    This is a small educational demonstration, not a production benchmark.
    """
    precisions, recalls = [], []
    eligible_users = []

    for user_id, group in ratings.groupby("userId"):
        relevant = group[group["rating"] >= 4]["movieId"].tolist()
        if len(relevant) >= 2:
            eligible_users.append((user_id, relevant))

    for user_id, relevant_ids in eligible_users:
        held_out = relevant_ids[-1]
        train_ratings = ratings[
            ~((ratings["userId"] == user_id) & (ratings["movieId"] == held_out))
        ]

        recommendations = recommend_for_user(
            user_id, movies, train_ratings,
            build_content_model(movies)[2], top_n=top_n
        )
        recommended_ids = recommendations["movieId"].tolist() \
            if "movieId" in recommendations.columns else []

        p, r = precision_recall_at_k(recommended_ids, [held_out], k=top_n)
        precisions.append(p)
        recalls.append(r)

    if precisions:
        print(f"Precision@{top_n}: {np.mean(precisions):.3f}")
        print(f"Recall@{top_n}:    {np.mean(recalls):.3f}")
    else:
        print("Not enough user history for holdout evaluation.")


def linear_regression_rating_demo(movies, ratings):
    """
    Optional rating-prediction experiment to demonstrate LinearRegression.
    Predicts ratings from release year and genre count.
    It is an educational side experiment, not the main recommender.
    """
    data = ratings.merge(
        movies[["movieId", "release_year", "genres"]], on="movieId"
    ).copy()
    data["genre_count"] = data["genres"].apply(
        lambda value: len(str(value).split())
    )
    X = data[["release_year", "genre_count"]]
    y = data["rating"]

    if len(data) < 5:
        print("Not enough rows for Linear Regression demonstration.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE
    )
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    mae = mean_absolute_error(y_test, predictions)
    print("\nLINEAR REGRESSION RATING-PREDICTION DEMO")
    print("RMSE:", round(rmse, 3))
    print("MAE:", round(mae, 3))


# ============================================================
# STEP 7: COMMUNICATION & VISUALIZATION
# ============================================================
def show_project_summary(movies, ratings):
    print("\n" + "=" * 55)
    print("       MOVIE RECOMMENDATION INTELLIGENCE SYSTEM")
    print("=" * 55)
    print(f"Movies available : {movies['movieId'].nunique()}")
    print(f"Users available  : {ratings['userId'].nunique()}")
    print(f"Ratings collected: {len(ratings)}")
    print("\nTop popular movies:")
    print(popularity_recommendations(movies, ratings, top_n=5).to_string(index=False))
    print("\nCharts are available in outputs/graphs/")
    print("=" * 55)


# ============================================================
# STEP 8: DECISION & DEPLOYMENT
# ============================================================
def recommendation_engine(user_id=None, movie_title=None, top_n=5):
    """
    Main deployment-style wrapper.
    Give a user_id for personalized recommendations or movie_title
    for similar-movie recommendations.
    """
    movies, ratings = create_sample_data()
    movies, ratings, _ = clean_data(movies, ratings)
    _, _, similarity_matrix = build_content_model(movies)

    if movie_title:
        return recommend_similar_movies(
            movie_title, movies, similarity_matrix, top_n
        )
    if user_id is not None:
        return recommend_for_user(
            user_id, movies, ratings, similarity_matrix, top_n
        )
    return popularity_recommendations(movies, ratings, top_n)


# ============================================================
# RUN THE COMPLETE PROJECT
# ============================================================
def main():
    print("STEP 1: Problem understood.")
    movies, ratings = create_sample_data()

    print("\nSTEP 2: Sample data collected.")
    print("\nMovies preview:\n", movies.head())
    print("\nRatings preview:\n", ratings.head())

    print("\nSTEP 3: Preparing data...")
    movies, ratings, merged = clean_data(movies, ratings)

    print("\nSTEP 4: Performing EDA...")
    perform_eda(movies, ratings, merged)

    print("\nSTEP 5: Building recommendation models...")
    _, _, similarity_matrix = build_content_model(movies)

    print("\nSimilar movies to Interstellar:")
    print(recommend_similar_movies(
        "Interstellar", movies, similarity_matrix, top_n=5
    ).to_string(index=False))

    print("\nPersonalized recommendations for user 101:")
    print(recommend_for_user(
        101, movies, ratings, similarity_matrix, top_n=5
    ).to_string(index=False))

    print("\nSTEP 6: Evaluating recommendations...")
    evaluate_content_model(movies, ratings, top_n=5)
    linear_regression_rating_demo(movies, ratings)

    print("\nSTEP 7: Communicating results...")
    show_project_summary(movies, ratings)

    print("\nSTEP 8: Deployment-style function is ready.")
    print("Example: recommendation_engine(user_id=101, top_n=5)")
    print("Example: recommendation_engine(movie_title='Interstellar', top_n=5)")
    print("\nPROJECT EXECUTION COMPLETED.")


if __name__ == "__main__":
    main()
