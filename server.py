import os
import uvicorn
from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from your frontend
origins = [
    "https://spotify-frame-1.onrender.com",  # Your frontend URL
    "https://spotify-frame-dhso.onrender.com",  # Allowing itself (for debugging)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows only specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running!"}

@app.get("/currently-playing")
def get_current_song():
    SPOTIFY_API_URL = "https://api.spotify.com/v1/me/player/currently-playing"

    # Your actual Spotify credentials
    SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
    SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
    SPOTIFY_REFRESH_TOKEN = "AQBPdyZ42yIk6HftPQLOkA8ehvKzXjEvkoPe9SnUILl_u_kC7tl7hDSLAAbiY5vTABdcBkZaqpdfUH-p8s4MyHCtBVNnPyg2-88srqu7nkVQ_3YAlWk7rgbTzc2rdz5rcwU"

    # Use the refresh token function to get a fresh access token
    access_token = refresh_spotify_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN)
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

def refresh_spotify_token(client_id, client_secret, refresh_token):
    refresh_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(refresh_url, data=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Explicitly binding to 10000 for Render
    uvicorn.run(app, host="0.0.0.0", port=port)