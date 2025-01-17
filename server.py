import uvicorn
import requests
from fastapi import FastAPI
import os

app = FastAPI()

# Spotify API Credentials
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
SPOTIFY_REFRESH_TOKEN = "AQBPdyZ42yIk6HftPQLOkA8ehvKzXjEvkoPe9SnUILl_u_kC7tl7hDSLAAbiY5vTABdcBkZaqpdfUH-p8s4MyHCtBVNnPyg2-88srqu7nkVQ_3YAlWk7rgbTzc2rdz5rcwU"

# Stores the latest valid access token
spotify_access_token = None


def refresh_spotify_token():
    """
    Refreshes the Spotify access token using the stored refresh token.
    """
    global spotify_access_token

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }

    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        spotify_access_token = response.json().get("access_token")
        print(f"New Spotify Access Token: {spotify_access_token}")
    else:
        print(f"Error refreshing token: {response.json()}")


@app.get("/")
def read_root():
    return {"message": "Server is running!"}


@app.get("/currently-playing")
def get_current_song():
    """
    Fetches the currently playing song and album artwork from Spotify.
    """
    global spotify_access_token

    # If there's no access token yet, refresh it
    if not spotify_access_token:
        refresh_spotify_token()

    headers = {"Authorization": f"Bearer {spotify_access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if response.status_code == 401:  # Token expired
        refresh_spotify_token()
        headers = {"Authorization": f"Bearer {spotify_access_token}"}
        response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "item" in data:
            song_name = data["item"]["name"]
            artist_name = data["item"]["artists"][0]["name"]
            album_art = data["item"]["album"]["images"][0]["url"]

            return {
                "song": song_name,
                "artist": artist_name,
                "album_art": album_art
            }
        else:
            return {"message": "No song is currently playing."}
    else:
        return {"error": "Failed to fetch currently playing song.", "details": response.json()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)