import os
import requests
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running!"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT isn't set
    uvicorn.run(app, host="0.0.0.0", port=port)

# Spotify API endpoint
SPOTIFY_API_URL = "https://api.spotify.com/v1/me/player/currently-playing"

# Supabase credentials
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co/rest/v1/"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"

# Spotify refresh token (stored in Supabase)
SPOTIFY_REFRESH_TOKEN = "AQBPdyZ42yIk6HftPQLOkA8ehvKzXjEvkoPe9SnUILl_u_kC7tl7hDSLAAbiY5vTABdcBkZaqpdfUH-p8s4MyHCtBVNnPyg2-88srqu7nkVQ_3YAlWk7rgbTzc2rdz5rcwU"

# Spotify client credentials
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"

# Function to refresh Spotify token
def refresh_spotify_token():
    refresh_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(refresh_url, data=payload)

    if response.status_code == 200:
        new_token = response.json().get("access_token")
        return new_token
    else:
        return None

# API Route to get currently playing song
@app.get("/currently-playing")
def get_current_song():
    access_token = refresh_spotify_token()
    if not access_token:
        return {"error": "Failed to refresh token"}

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_API_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        song_name = data["item"]["name"]
        album_art = data["item"]["album"]["images"][0]["url"]
        return {"song": song_name, "album_art": album_art}
    else:
        return {"error": "No song currently playing"}