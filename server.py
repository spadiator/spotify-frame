import os
import uvicorn
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running!"}

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