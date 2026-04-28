from flask import Flask, jsonify, request, send_from_directory  
from flask_cors import CORS
import joblib
import pandas as pd
import requests
import toml

app = Flask(__name__)
CORS(app)

# =========================
# LOAD SECRET (API KEY)
# =========================
secrets = toml.load(".streamlit/secrets.toml")
API_KEY = secrets["TMDB_API_KEY"]

# =========================
# LOAD DATA
# =========================
movies_list = joblib.load("movie_data.joblib")
similarity = joblib.load("similarity.joblib")

print("✅ Movies Loaded:", len(movies_list))

# =========================
# FETCH POSTER FROM TMDB
# =========================
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
        data = requests.get(url).json()

        poster_path = data.get("poster_path")

        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except:
        pass

    return ""

# =========================
# FETCH HOMEPAGE FROM TMDB
# =========================

def fetch_homepage(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
        data = requests.get(url).json()

        return data.get("homepage")
    except:
        return None


# =========================
# 🔥 GET ALL MOVIES (FOR SEARCH)
# =========================
@app.route("/movies", methods=["GET"])
def get_movies():
    try:
        movie_names = movies_list['title'].dropna().tolist()
        return jsonify(movie_names)
    except:
        return jsonify([])

# =========================
# RECOMMEND BY MOVIE
# =========================
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        movie = request.json.get("movie")

        movie_data = movies_list[movies_list['title'] == movie]

        if movie_data.empty:
            return jsonify([])

        idx = movie_data.index[0]
        distances = similarity[idx]

        movies_sorted = sorted(
            list(enumerate(distances)),
            reverse=True,
            key=lambda x: x[1]
        )[1:11]

        result = []

        for i in movies_sorted:
            data = movies_list.iloc[i[0]]

            result.append({
                "title": data.title,
                "poster": fetch_poster(data.movie_id),
                "rating": data.rating,
                "runtime": data.runtime,
                "overview": data.overview,
                "language": data.original_language,
                "homepage": fetch_homepage(data.movie_id)
            })

        return jsonify(result)

    except Exception as e:
        print("Error:", e)
        return jsonify([])

# =========================
# RECOMMEND BY MOOD
# =========================
@app.route("/mood", methods=["POST"])
def mood():
    try:
        mood_map = {
            "Happy 😄": ["Comedy", "Family", "Animation"],
            "Sad 😢": ["Drama"],
            "Romantic ❤️": ["Romance"],
            "Excited 🤩": ["Action", "Thriller"],
            "Scared 👻": ["Horror"],
            "Motivated 💪": ["History", "Drama", "Biography"],
            "Relaxed 🌙": ["Fantasy", "Family", "Music"]
        }

        mood = request.json.get("mood")
        genres = mood_map.get(mood, [])

        mood_movies = movies_list[
            movies_list['genres'].apply(
                lambda x: any(g in str(x) for g in genres)
            )
        ]

        if len(mood_movies) == 0:
            return jsonify([])

        mood_movies = mood_movies.sample(min(10, len(mood_movies)))

        result = []

        for _, data in mood_movies.iterrows():
            result.append({
                "title": data.title,
                "poster": fetch_poster(data.movie_id),
                "rating": data.rating,
                "runtime": data.runtime,
                "overview": data.overview,
                "language": data.original_language,
                "homepage": fetch_homepage(data.movie_id)
            })

        return jsonify(result)

    except Exception as e:
        print("Error:", e)
        return jsonify([])

# =========================
# HOME PAGE (ADD THIS HERE)
# =========================
@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
