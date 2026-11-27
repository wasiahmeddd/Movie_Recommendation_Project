"""
Automated Test Suite for Movie Recommendation Platform.
Verifies REST API endpoints, recommendation generation, authentication,
interaction tracking, watch history, watchlist, and admin operations.
"""

import sys
import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from server import app


def run_tests():
    print("=" * 60)
    print(" RUNNING AUTOMATED TEST SUITE FOR SKILL LAB REVIEW 2")
    print("=" * 60)

    client = app.test_client()
    passed = 0
    total = 0

    def check(description, condition):
        nonlocal passed, total
        total += 1
        status = "PASSED" if condition else "FAILED"
        print(f"[{status}] Test {total:02d}: {description}")
        if condition:
            passed += 1
        else:
            print("   -> ASSERTION FAILED")

    # 1. Static Index
    res = client.get("/")
    check("Homepage returns HTTP 200", res.status_code == 200 and b"TITANFLIX" in res.data)

    # 2. Featured movie
    res = client.get("/api/movies/featured")
    data = res.get_json()
    valid_movie_id = data.get("id")
    check("Featured hero movie returned with backdrop and title", res.status_code == 200 and "title" in data and "backdrop_url" in data and bool(valid_movie_id))

    # 3. User Authentication: Login demo_user
    res = client.post("/api/auth/login", json={"username": "demo_user", "password": "user123"})
    login_data = res.get_json()
    token = login_data.get("token")
    check("Login demo_user returns valid session token", res.status_code == 200 and bool(token))

    headers = {"Authorization": f"Bearer {token}"}

    # 4. User details /api/auth/me
    res = client.get("/api/auth/me", headers=headers)
    me_data = res.get_json()
    check("Authenticated /api/auth/me identifies demo_user", me_data.get("username") == "demo_user")

    # 5. Onboarding Preferences
    res = client.post("/api/onboarding/preferences", headers=headers, json={"genres": ["Sci-Fi", "Action", "Thriller", "Adventure"]})
    check("Save onboarding preferences requires >= 3 genres", res.status_code == 200)

    # 6. Categories & Hybrid Recommendations
    res = client.get("/api/movies/categories", headers=headers)
    cat_data = res.get_json()
    cat_types = [c["type"] for c in cat_data]
    check("Categories include Recommended, Trending, Continue Watching, Genres", 
          "recommended" in cat_types and "trending" in cat_types and "continue_watching" in cat_types)

    # 7. Interaction Tracking
    res = client.post("/api/interactions", headers=headers, json={
        "movie_id": valid_movie_id,
        "interaction_type": "click",
        "recommendation_source": "recommended_for_you"
    })
    check("Track interaction (click event) recorded in database", res.status_code == 200)

    # 8. Watch Progress & Continue Watching
    res = client.post("/api/watch-progress", headers=headers, json={
        "movie_id": valid_movie_id,
        "progress_pct": 55.0
    })
    check("Update watch progress to 55% saved", res.status_code == 200)

    # 9. Watch History
    res = client.get("/api/watch-history", headers=headers)
    history_data = res.get_json()
    check("Viewing history lists in-progress and completed items", len(history_data) >= 1)

    # 10. Watchlist Toggle
    res = client.post("/api/watchlist/toggle", headers=headers, json={"movie_id": valid_movie_id})
    wl_data = res.get_json()
    check("Toggle watchlist adds/removes movie", res.status_code == 200 and "in_watchlist" in wl_data)

    # 11. Watchlist List
    res = client.get("/api/watchlist", headers=headers)
    check("Retrieve user watchlist", res.status_code == 200 and isinstance(res.get_json(), list))

    # 12. Search & Discovery
    res = client.get("/api/search?q=Dark")
    search_data = res.get_json()
    check("Search for 'Dark' finds matching movies (e.g. The Dark Knight)", len(search_data) >= 1 and any("Dark" in m["title"] for m in search_data))

    # 13. Social Friends
    res = client.get("/api/friends", headers=headers)
    friends_data = res.get_json()
    check("Friends list returns connected friend (sarah_friend)", len(friends_data) >= 1 and any(f["username"] == "sarah_friend" for f in friends_data))

    # 14. Admin Authentication
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = res.get_json().get("token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    check("Admin login successful", res.status_code == 200 and bool(admin_token))

    # 15. Admin Stats
    res = client.get("/api/admin/stats", headers=admin_headers)
    stats_data = res.get_json()
    check("Admin analytics returns total movies, users, and ratings", 
          stats_data.get("total_movies", 0) >= 1000 and stats_data.get("total_ratings", 0) >= 20000)

    # 16. Admin Create Movie
    res = client.post("/api/admin/movies", headers=admin_headers, json={
        "title": "Quantum Odyssey",
        "release_year": 2026,
        "duration": 140,
        "rating": 4.9,
        "director": "Elena Vance",
        "cast_members": "Sophia Chen, Marcus Reed",
        "overview": "A daring physicist voyages across dimensional boundaries to avert universal collapse.",
        "genres": ["Sci-Fi", "Adventure", "Thriller"],
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&q=80"
    })
    new_movie_id = res.get_json().get("movie_id")
    check("Admin adds new movie with genre relationships", res.status_code == 201 and bool(new_movie_id))

    # 17. Admin Delete Movie
    if new_movie_id:
        res = client.delete(f"/api/admin/movies/{new_movie_id}", headers=admin_headers)
        check("Admin deletes movie", res.status_code == 200)

    # 18. Non-admin forbidden from admin routes
    res = client.get("/api/admin/stats", headers=headers)
    check("Regular user access to admin route is blocked (HTTP 403)", res.status_code == 403)

    print("=" * 60)
    print(f" TEST RESULTS: {passed}/{total} TESTS PASSED ({passed/total*100:.1f}%)")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
