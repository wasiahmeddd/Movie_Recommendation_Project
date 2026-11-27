"""
Dataset Downloader and Importer for Movie Recommendation Platform.
Supports MovieLens (100k / ml-latest-small, 1M) and TMDB metadata enrichment.
Includes automated download, parsing, genre mapping, rating aggregation,
high-resolution poster/backdrop assignment, and demo user seeding.
"""

import os
import sys
import ssl
import zipfile
import urllib.request
import csv
import re
from datetime import datetime

# Adjust path to import database module
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from database import init_db, get_db_connection, hash_password

DATASETS_DIR = CURRENT_DIR
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
ZIP_PATH = os.path.join(DATASETS_DIR, "ml-latest-small.zip")
EXTRACT_DIR = os.path.join(DATASETS_DIR, "ml-latest-small")

# High-resolution poster and backdrop mappings for prominent movies
ENRICHED_MOVIES = {
    "Inception": {
        "poster_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
        "overview": "Cobb, a skilled thief who steals corporate secrets through the use of dream-sharing technology, is given the inverse task of planting an idea into the mind of a CEO.",
        "director": "Christopher Nolan",
        "cast_members": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy",
        "duration": 148,
    },
    "Interstellar": {
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/xJHokMbljvjADYdit5fK5VQsXEG.jpg",
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        "director": "Christopher Nolan",
        "cast_members": "Matthew McConaughey, Anne Hathaway, Jessica Chastain, Michael Caine",
        "duration": 169,
    },
    "The Dark Knight": {
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/dqK9Hag1054tghRQSqLSfrkvQnA.jpg",
        "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
        "director": "Christopher Nolan",
        "cast_members": "Christian Bale, Heath Ledger, Aaron Eckhart, Michael Caine",
        "duration": 152,
    },
    "The Matrix": {
        "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/7c9UVPPiTPltouxShY9fKqURWZT.jpg",
        "overview": "Set in the 22nd century, The Matrix tells the story of a computer hacker who joins a group of underground insurgents fighting the vast and powerful computers who now rule the earth.",
        "director": "Lana Wachowski, Lilly Wachowski",
        "cast_members": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss, Hugo Weaving",
        "duration": 136,
    },
    "Pulp Fiction": {
        "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFnGhFvlW147Ha50slSuTvS.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
        "overview": "A burger-loving hit man, his philosophical partner, a drug-addled gangster's moll and a washed-up boxer converge in this sprawling, comedic crime caper.",
        "director": "Quentin Tarantino",
        "cast_members": "John Travolta, Samuel L. Jackson, Uma Thurman, Bruce Willis",
        "duration": 154,
    },
    "The Shawshank Redemption": {
        "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/kXfqcdQKsToO0OUXHcrrNCHDBzO.jpg",
        "overview": "Framed in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison, where he puts his accounting skills to work for an amoral warden.",
        "director": "Frank Darabont",
        "cast_members": "Tim Robbins, Morgan Freeman, Bob Gunton, William Sadler",
        "duration": 142,
    },
    "Forrest Gump": {
        "poster_url": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/qdIMhmSlMAeoEDsv0v35bVlmhqU.jpg",
        "overview": "A man with a low IQ has accomplished great things in his life and been present during significant historic events—in each case, far exceeding what anyone imagined he could do.",
        "director": "Robert Zemeckis",
        "cast_members": "Tom Hanks, Robin Wright, Gary Sinise, Sally Field",
        "duration": 142,
    },
    "Fight Club": {
        "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
        "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy. Their concept catches on, with underground 'fight clubs' forming in every town.",
        "director": "David Fincher",
        "cast_members": "Edward Norton, Brad Pitt, Helena Bonham Carter, Meat Loaf",
        "duration": 139,
    },
    "The Godfather": {
        "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/tmU7GeKVybMWFButWEGl2M4GeiP.jpg",
        "overview": "Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family. When organized crime family patriarch, Vito Corleone barely survives an attempt on his life, his youngest son steps in.",
        "director": "Francis Ford Coppola",
        "cast_members": "Marlon Brando, Al Pacino, James Caan, Robert Duvall",
        "duration": 175,
    },
    "Avengers: Infinity War": {
        "poster_url": "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/mDfJG3LC3Dqb67AZ52x3Z0jQ0uB.jpg",
        "overview": "As the Avengers and their allies have continued to protect the world from threats too large for any one hero to handle, a new danger has emerged from the cosmic shadows: Thanos.",
        "director": "Anthony Russo, Joe Russo",
        "cast_members": "Robert Downey Jr., Chris Hemsworth, Mark Ruffalo, Chris Evans",
        "duration": 149,
    },
    "The Avengers": {
        "poster_url": "https://image.tmdb.org/t/p/w500/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/9BBTo63ANSmhC4e6r62OJFuK2GL.jpg",
        "overview": "When an unexpected enemy emerges and threatens global safety and security, Nick Fury, director of the international peacekeeping agency known as S.H.I.E.L.D., finds himself in need of a team to pull the world back from the brink.",
        "director": "Joss Whedon",
        "cast_members": "Robert Downey Jr., Chris Evans, Mark Ruffalo, Chris Hemsworth",
        "duration": 143,
    },
    "Gladiator": {
        "poster_url": "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/Ar7sFvh2ZfG9R1f02BaeJ4e7b4V.jpg",
        "overview": "In the year 180, the death of emperor Marcus Aurelius throws the Roman Empire into turmoil. Maximus Decimus Meridius, one of the Roman army's most capable generals, is betrayed and forced into slavery as a gladiator.",
        "director": "Ridley Scott",
        "cast_members": "Russell Crowe, Joaquin Phoenix, Connie Nielsen, Oliver Reed",
        "duration": 155,
    },
    "Titanic": {
        "poster_url": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/6VmFqZwQIISIAzUeexm2BTgQ22A.jpg",
        "overview": "101-year-old Rose DeWitt Bukater tells the story of her life aboard the Titanic, 84 years later. A young Rose boards the ship with her mother and fiancé. Meanwhile, Jack Dawson wins third-class tickets.",
        "director": "James Cameron",
        "cast_members": "Leonardo DiCaprio, Kate Winslet, Billy Zane, Kathy Bates",
        "duration": 194,
    },
    "Jurassic Park": {
        "poster_url": "https://image.tmdb.org/t/p/w500/oU7Oq2kFAAlGqbU4VoAE36g4hoI.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/8I37NtDffNV7AZlDa7uDvvqhovU.jpg",
        "overview": "A wealthy entrepreneur secretly creates a theme park featuring living dinosaurs drawn from prehistoric DNA. Before opening it to the public, he invites a top paleontologist and a mathematician to experience the park.",
        "director": "Steven Spielberg",
        "cast_members": "Sam Neill, Laura Dern, Jeff Goldblum, Richard Attenborough",
        "duration": 127,
    },
    "The Silence of the Lambs": {
        "poster_url": "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXUNAq.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/mfwq2nMBzArGQay6E1amMW4mUFe.jpg",
        "overview": "Clarice Starling is a top student at the FBI's training academy. Jack Crawford wants Clarice to interview Dr. Hannibal Lecter, a brilliant psychiatrist who is also a violent psychopath.",
        "director": "Jonathan Demme",
        "cast_members": "Jodie Foster, Anthony Hopkins, Scott Glenn, Ted Levine",
        "duration": 118,
    },
    "Star Wars: Episode IV - A New Hope": {
        "poster_url": "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/zqkmTXzjkAgPnDCV4H800AHwG2U.jpg",
        "overview": "Princess Leia is captured and held hostage by the evil Imperial forces in their effort to take over the galactic Empire. Venturesome Luke Skywalker and dashing captain Han Solo team together with the lovable robot duo R2-D2 and C-3PO.",
        "director": "George Lucas",
        "cast_members": "Mark Hamill, Harrison Ford, Carrie Fisher, Peter Cushing",
        "duration": 121,
    },
    "Toy Story": {
        "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/lxD5ak7BOx085IOVIOTzG9vWYtK.jpg",
        "overview": "Led by Woody, Andy's toys live happily in his room until Andy's birthday brings Buzz Lightyear onto the scene. Afraid of losing his place in Andy's heart, Woody plots against Buzz.",
        "director": "John Lasseter",
        "cast_members": "Tom Hanks, Tim Allen, Don Rickles, Jim Varney",
        "duration": 81,
    },
    "Finding Nemo": {
        "poster_url": "https://image.tmdb.org/t/p/w500/ggQzk1zcv6R8Tq8J2s1o6W0pX0U.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/a4BfxRK8RJbt5nQ9Z5b6j2GZ1e.jpg",
        "overview": "Nemo, an adventurous young clownfish, is unexpectedly taken from his Great Barrier Reef home and thrust into a fish tank in a dentist's office. It's up to his worrisome father Marlin and a friendly forgetful fish named Dory to rescue him.",
        "director": "Andrew Stanton",
        "cast_members": "Albert Brooks, Ellen DeGeneres, Alexander Gould, Willem Dafoe",
        "duration": 100,
    },
    "Coco": {
        "poster_url": "https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/askg3SMvhqEl4OL52YuvdtY40Yb.jpg",
        "overview": "Despite his family's baffling generations-old ban on music, Miguel dreams of becoming an accomplished musician like his idol, Ernesto de la Cruz. Desperate to prove his talent, Miguel finds himself in the stunning Land of the Dead.",
        "director": "Lee Unkrich",
        "cast_members": "Anthony Gonzalez, Gael García Bernal, Benjamin Bratt, Alanna Ubach",
        "duration": 105,
    },
    "Joker": {
        "poster_url": "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/f5F4cRhQdU3bu0NednTJR6x92UR.jpg",
        "overview": "During the 1980s, a failed stand-up comedian is driven insane and turns to a life of crime and chaos in Gotham City while becoming an infamous psychopathic crime figure.",
        "director": "Todd Phillips",
        "cast_members": "Joaquin Phoenix, Robert De Niro, Zazie Beetz, Frances Conroy",
        "duration": 122,
    },
    "Dune": {
        "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/eeijXm3554UtMVXYqpMTZjo9P2q.jpg",
        "overview": "Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.",
        "director": "Denis Villeneuve",
        "cast_members": "Timothée Chalamet, Rebecca Ferguson, Oscar Isaac, Zendaya",
        "duration": 155,
    },
    "Oppenheimer": {
        "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/rM5Y09xC99JeApXWZZSIh42XBqZ.jpg",
        "overview": "The story of J. Robert Oppenheimer's role in the development of the atomic bomb during World War II, examining the scientific triumph and moral dilemma of creating humanity's ultimate weapon.",
        "director": "Christopher Nolan",
        "cast_members": "Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr.",
        "duration": 180,
    },
    "Spider-Man: Into the Spider-Verse": {
        "poster_url": "https://image.tmdb.org/t/p/w500/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/7d6woWBsigYrqqRvd29vyokuh57.jpg",
        "overview": "Miles Morales is juggling his life between being a high school student and being a spider-man. When Wilson 'Kingpin' Fisk uses a super collider, others from across the Spider-Verse are transported to this dimension.",
        "director": "Bob Persichetti, Peter Ramsey, Rodney Rothman",
        "cast_members": "Shameik Moore, Jake Johnson, Hailee Steinfeld, Mahershala Ali",
        "duration": 117,
    },
    "Parasite": {
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/hiKmpZMGZsrkA3cdce8a7Dpos1j.jpg",
        "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
        "director": "Bong Joon-ho",
        "cast_members": "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong, Choi Woo-shik",
        "duration": 132,
    },
    "Whiplash": {
        "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/6bbZ6XyvgfjhQwfplHVpj7IXemw.jpg",
        "overview": "Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at any cost, testing the limits of sanity and artistic passion.",
        "director": "Damien Chazelle",
        "cast_members": "Miles Teller, J.K. Simmons, Paul Reiser, Melissa Benoist",
        "duration": 107,
    },
    "La La Land": {
        "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkVJb0Rf0.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/nlPCdZlDmG1oKn1N4w1n2XUe51Y.jpg",
        "overview": "Mia, an aspiring actress, and Sebastian, a dedicated jazz musician, are struggling to make ends meet in a city known for crushing hopes and breaking hearts.",
        "director": "Damien Chazelle",
        "cast_members": "Ryan Gosling, Emma Stone, John Legend, J.K. Simmons",
        "duration": 128,
    },
    "The Wolf of Wall Street": {
        "poster_url": "https://image.tmdb.org/t/p/w500/34m2tygAYBGqA9MXKhRDtzYd4MR.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/cWUOv3H7YFwvKeRwGdY3IoIlflS.jpg",
        "overview": "A New York stockbroker refuses to cooperate in a large securities fraud case that involves corruption on Wall Street, the corporate banking world and mob infiltration.",
        "director": "Martin Scorsese",
        "cast_members": "Leonardo DiCaprio, Jonah Hill, Margot Robbie, Matthew McConaughey",
        "duration": 180,
    },
    "Alien": {
        "poster_url": "https://image.tmdb.org/t/p/w500/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/AmR3JG1DYhf5IHQQUgQn5v94Pq3.jpg",
        "overview": "During its return to the earth, commercial spaceship Nostromo receives a transmission that may be a distress call. The crew explores an alien vessel where a lethal creature is unleashed.",
        "director": "Ridley Scott",
        "cast_members": "Sigourney Weaver, Tom Skerritt, John Hurt, Veronica Cartwright",
        "duration": 117,
    },
    "The Shining": {
        "poster_url": "https://image.tmdb.org/t/p/w500/b33nnKl1GSJbao4l3fZDDqsMx0F.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/mmd1HnuvAzFc4iYYl9PioegBEfp.jpg",
        "overview": "Jack Torrance accepts a caretaker job at the Overlook Hotel in Colorado, where he, his wife Wendy and their son Danny must live isolated from the rest of the world for the winter.",
        "director": "Stanley Kubrick",
        "cast_members": "Jack Nicholson, Shelley Duvall, Danny Lloyd, Scatman Crothers",
        "duration": 146,
    },
    "Schindler's List": {
        "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/zb6fM1CX41D9r69hdYvrb0D0jT.jpg",
        "overview": "The true story of how businessman Oskar Schindler saved over a thousand Jewish lives from the Holocaust while running a factory in Nazi-occupied Poland.",
        "director": "Steven Spielberg",
        "cast_members": "Liam Neeson, Ben Kingsley, Ralph Fiennes, Caroline Goodall",
        "duration": 195,
    },
}

# Generic high-quality poster fallback pool for other movies categorized by genre
GENRE_POSTER_FALLBACKS = {
    "Action": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&q=80",
    "Adventure": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&q=80",
    "Animation": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500&q=80",
    "Comedy": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=500&q=80",
    "Crime": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&q=80",
    "Documentary": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80",
    "Drama": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=500&q=80",
    "Family": "https://images.unsplash.com/photo-1511895426328-dc8714191300?w=500&q=80",
    "Fantasy": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&q=80",
    "History": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?w=500&q=80",
    "Horror": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=500&q=80",
    "Music": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&q=80",
    "Mystery": "https://images.unsplash.com/photo-1519638399535-1b036603ac77?w=500&q=80",
    "Romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=500&q=80",
    "Sci-Fi": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&q=80",
    "Thriller": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=500&q=80",
    "War": "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=500&q=80",
    "Western": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=500&q=80",
}


def download_dataset():
    """Downloads MovieLens small zip if not already present."""
    os.makedirs(DATASETS_DIR, exist_ok=True)
    if os.path.exists(EXTRACT_DIR):
        print(f"Dataset directory '{EXTRACT_DIR}' already exists. Skipping download.")
        return True

    if not os.path.exists(ZIP_PATH):
        print(f"Downloading MovieLens dataset from: {MOVIELENS_URL} ...")
        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(MOVIELENS_URL, context=ctx, timeout=30) as response, open(ZIP_PATH, 'wb') as out_file:
                total_bytes = 0
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    total_bytes += len(chunk)
                print(f"Downloaded {total_bytes / (1024 * 1024):.2f} MB successfully.")
        except Exception as e:
            print(f"Error downloading MovieLens: {e}")
            return False

    print(f"Extracting '{ZIP_PATH}'...")
    try:
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(DATASETS_DIR)
        print(f"Extraction complete to: {EXTRACT_DIR}")
        return True
    except Exception as e:
        print(f"Error extracting zip: {e}")
        return False


def clean_title_and_year(raw_title: str):
    """Parses 'Movie Name (YYYY)' into title and integer year."""
    raw_title = raw_title.strip()
    match = re.search(r"\s*\((\d{4})\)\s*$", raw_title)
    if match:
        year = int(match.group(1))
        title = raw_title[:match.start()].strip()
    else:
        year = 2000
        title = raw_title
    return title, year


def import_movielens_data():
    """Reads CSVs from MovieLens and populates the database."""
    movies_csv = os.path.join(EXTRACT_DIR, "movies.csv")
    ratings_csv = os.path.join(EXTRACT_DIR, "ratings.csv")
    tags_csv = os.path.join(EXTRACT_DIR, "tags.csv")
    links_csv = os.path.join(EXTRACT_DIR, "links.csv")

    if not os.path.exists(movies_csv) or not os.path.exists(ratings_csv):
        print("Required CSV files not found. Please run download_dataset() first.")
        return

    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Step 1: Precompute movie ratings summary from ratings.csv
    print("Aggregating movie ratings...")
    movie_ratings = {} # movie_id -> [sum, count]
    ratings_rows = []
    with open(ratings_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m_id = int(row["movieId"])
            u_id = int(row["userId"])
            rating = float(row["rating"])
            ts = int(row.get("timestamp", 0))

            if m_id not in movie_ratings:
                movie_ratings[m_id] = [0.0, 0]
            movie_ratings[m_id][0] += rating
            movie_ratings[m_id][1] += 1

            # Keep ratings for up to first 200 users for quick seeding
            if u_id <= 200:
                ratings_rows.append((u_id, m_id, rating, ts))

    print(f"Processed ratings for {len(movie_ratings)} distinct movies.")

    # Step 2: Read tags.csv to collect keywords
    print("Collecting tags...")
    movie_tags = {}
    if os.path.exists(tags_csv):
        with open(tags_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                m_id = int(row["movieId"])
                tag = row["tag"].strip()
                if tag:
                    if m_id not in movie_tags:
                        movie_tags[m_id] = []
                    if len(movie_tags[m_id]) < 5:
                        movie_tags[m_id].append(tag)

    # Step 3: Read links.csv for tmdbIds
    print("Mapping TMDB IDs...")
    movie_tmdb = {}
    if os.path.exists(links_csv):
        with open(links_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                m_id = int(row["movieId"])
                tmdb_id = row.get("tmdbId")
                if tmdb_id and tmdb_id.isdigit():
                    movie_tmdb[m_id] = int(tmdb_id)

    # Step 4: Populate genres & movies
    print("Inserting genres and movies...")
    genre_cache = {} # name -> id
    
    # Pre-populate all standard streaming genres
    standard_genres = [
        "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", 
        "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Musical",
        "Mystery", "Romance", "Sci-Fi", "Science Fiction", "Thriller", "War", "Western"
    ]
    for g in standard_genres:
        cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g,))
    conn.commit()

    cursor.execute("SELECT id, name FROM genres")
    for r in cursor.fetchall():
        genre_cache[r["name"].lower()] = r["id"]

    inserted_movies = 0
    movie_id_map = {} # movielens_id -> database movie_id

    # Sort movies to prioritize those with higher ratings count first
    raw_movies = []
    with open(movies_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m_id = int(row["movieId"])
            title_raw = row["title"]
            genres_raw = row["genres"]
            rating_info = movie_ratings.get(m_id, [0.0, 0])
            raw_movies.append({
                "movielens_id": m_id,
                "title_raw": title_raw,
                "genres_raw": genres_raw,
                "avg_rating": round(rating_info[0] / rating_info[1], 2) if rating_info[1] > 0 else 3.5,
                "rating_count": rating_info[1]
            })

    # Sort movies: enriched or high rating count first, load up to 1,200 top movies
    # for lightning-fast performance and full coverage
    raw_movies.sort(key=lambda x: (
        x["title_raw"].split(" (")[0] in ENRICHED_MOVIES,
        x["rating_count"]
    ), reverse=True)

    target_movies = raw_movies[:1200]

    for item in target_movies:
        m_id = item["movielens_id"]
        title, year = clean_title_and_year(item["title_raw"])
        genres_list = [g.strip() for g in item["genres_raw"].split("|") if g.strip() and g.strip() != "(no genres listed)"]
        
        # Check if we have rich manual enrichment
        enrichment = ENRICHED_MOVIES.get(title)
        if not enrichment:
            # Check partial match
            for k, v in ENRICHED_MOVIES.items():
                if k.lower() == title.lower() or k.lower() in title.lower():
                    enrichment = v
                    break

        primary_genre = genres_list[0] if genres_list else "Drama"
        if primary_genre == "Sci-Fi":
            primary_genre_name = "Science Fiction"
        else:
            primary_genre_name = primary_genre

        if enrichment:
            poster_url = enrichment["poster_url"]
            backdrop_url = enrichment["backdrop_url"]
            overview = enrichment["overview"]
            director = enrichment["director"]
            cast_members = enrichment["cast_members"]
            duration = enrichment["duration"]
        else:
            poster_url = GENRE_POSTER_FALLBACKS.get(primary_genre, "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80")
            backdrop_url = "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&q=80"
            overview = f"A compelling {primary_genre_name.lower()} film set in {year}. Follow the emotional journey and gripping adventure as characters face pivotal challenges."
            director = "Acclaimed Filmmaker"
            cast_members = "Ensemble Cast"
            duration = 100 + (m_id % 45)

        tags_str = ", ".join(movie_tags.get(m_id, []))
        tmdb_val = movie_tmdb.get(m_id)

        cursor.execute("""
            INSERT OR REPLACE INTO movies (
                movielens_id, tmdb_id, title, release_year, duration, 
                overview, poster_url, backdrop_url, director, cast_members,
                average_rating, rating_count, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m_id, tmdb_val, title, year, duration,
            overview, poster_url, backdrop_url, director, cast_members,
            item["avg_rating"], item["rating_count"], tags_str
        ))
        db_movie_id = cursor.lastrowid
        movie_id_map[m_id] = db_movie_id
        inserted_movies += 1

        # Link genres
        for g_name in genres_list:
            g_key = g_name.lower()
            if g_key not in genre_cache:
                cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (g_name,))
                conn.commit()
                genre_cache[g_key] = cursor.lastrowid
            g_id = genre_cache[g_key]
            cursor.execute("INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)", (db_movie_id, g_id))

    conn.commit()
    print(f"Successfully inserted {inserted_movies} top movies into database.")

    # Step 5: Insert community users and ratings
    print("Inserting community users and user ratings...")
    valid_ratings = []
    for u_id, m_id, rating, ts in ratings_rows:
        if m_id in movie_id_map:
            valid_ratings.append((u_id, movie_id_map[m_id], rating, ts))

    # First ensure user IDs exist in users table so foreign keys pass cleanly
    user_ids = sorted(list(set(u_id for u_id, _, _, _ in valid_ratings)))
    user_records = [
        (uid, f"movielens_user_{uid}", f"user{uid}@movielens.org", hash_password(f"pass_{uid}"), "user")
        for uid in user_ids if uid > 3 # reserve 1, 2, 3 for admin, demo_user, sarah_friend
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO users (id, username, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, user_records)
    conn.commit()

    # Seed demo accounts first
    seed_demo_accounts(conn, movie_id_map)

    # Now insert ratings
    cursor.executemany("""
        INSERT OR IGNORE INTO ratings (user_id, movie_id, rating, timestamp)
        VALUES (?, ?, ?, ?)
    """, valid_ratings)
    conn.commit()
    print(f"Inserted {len(valid_ratings)} ratings.")

    conn.close()
    print("Dataset import and database initialization completed successfully!")


def seed_demo_accounts(conn, movie_id_map):
    """Creates ready-to-demonstrate demo user, admin, and social friend."""
    cursor = conn.cursor()
    print("Seeding demo accounts and review data...")

    # 1. Admin Account (admin / admin123)
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, username, email, password_hash, role)
        VALUES (1, 'admin', 'admin@netflix.com', ?, 'admin')
    """, (hash_password("admin123"),))

    # 2. Demo User (demo_user / user123)
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, username, email, password_hash, role)
        VALUES (2, 'demo_user', 'user@netflix.com', ?, 'user')
    """, (hash_password("user123"),))

    # 3. Friend User (sarah_friend / user123)
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, username, email, password_hash, role)
        VALUES (3, 'sarah_friend', 'sarah@gmail.com', ?, 'user')
    """, (hash_password("user123"),))

    # 4. Onboarding Preferences for demo_user (Sci-Fi, Action, Thriller, Drama)
    genres_demo = ["Sci-Fi", "Action", "Thriller", "Adventure"]
    for g in genres_demo:
        cursor.execute("INSERT OR IGNORE INTO user_preferences (user_id, genre) VALUES (2, ?)", (g,))

    # 5. Connect friends (demo_user <-> sarah_friend)
    cursor.execute("INSERT OR IGNORE INTO friends (user_id, friend_user_id) VALUES (2, 3)")
    cursor.execute("INSERT OR IGNORE INTO friends (user_id, friend_user_id) VALUES (3, 2)")
    cursor.execute("INSERT OR REPLACE INTO user_privacy_settings (user_id, share_activity_with_friends) VALUES (2, 1)")
    cursor.execute("INSERT OR REPLACE INTO user_privacy_settings (user_id, share_activity_with_friends) VALUES (3, 1)")

    # 6. Seed Watchlist for demo_user
    cursor.execute("SELECT id, title FROM movies LIMIT 25")
    sample_movies = cursor.fetchall()
    if len(sample_movies) >= 10:
        # Put 3 movies in watchlist
        cursor.execute("INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (2, ?)", (sample_movies[0]["id"],))
        cursor.execute("INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (2, ?)", (sample_movies[1]["id"],))
        cursor.execute("INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (2, ?)", (sample_movies[2]["id"],))

        # Put 3 movies in Continue Watching with distinct progress %
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (2, ?, 45.0, 0, datetime('now', '-2 hours'))
        """, (sample_movies[3]["id"],))
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (2, ?, 72.0, 0, datetime('now', '-5 hours'))
        """, (sample_movies[4]["id"],))
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (2, ?, 25.0, 0, datetime('now', '-1 day'))
        """, (sample_movies[5]["id"],))

        # Put 2 completed movies in watch history
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (2, ?, 100.0, 1, datetime('now', '-3 days'))
        """, (sample_movies[6]["id"],))
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (2, ?, 100.0, 1, datetime('now', '-4 days'))
        """, (sample_movies[7]["id"],))

        # Friend activity (sarah_friend watched movies 8 and 9)
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (3, ?, 100.0, 1, datetime('now', '-1 hour'))
        """, (sample_movies[8]["id"],))
        cursor.execute("""
            INSERT OR REPLACE INTO watch_history (user_id, movie_id, progress_pct, completed, last_watched_at)
            VALUES (3, ?, 85.0, 0, datetime('now', '-3 hours'))
        """, (sample_movies[9]["id"],))

        # Seed interaction tracking logs for demo_user
        cursor.execute("""
            INSERT INTO user_interactions (user_id, movie_id, interaction_type, completion_pct, recommendation_source)
            VALUES (2, ?, 'watch_progress', 45.0, 'trending_now')
        """, (sample_movies[3]["id"],))
        cursor.execute("""
            INSERT INTO user_interactions (user_id, movie_id, interaction_type, completion_pct, recommendation_source)
            VALUES (2, ?, 'like', 100.0, 'recommended_for_you')
        """, (sample_movies[6]["id"],))
        cursor.execute("""
            INSERT INTO user_interactions (user_id, movie_id, interaction_type, completion_pct, recommendation_source)
            VALUES (2, ?, 'watchlist_add', 0.0, 'hero_banner')
        """, (sample_movies[0]["id"],))

    conn.commit()
    print("Demo accounts and activities seeded.")


if __name__ == "__main__":
    success = download_dataset()
    if success:
        import_movielens_data()
