from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import requests
import asyncio

app = FastAPI()

# Store the latest Spotify access token
ACCESS_TOKEN = "YOUR_SPOTIFY_ACCESS_TOKEN"
REFRESH_TOKEN = "YOUR_SPOTIFY_REFRESH_TOKEN"
CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"

async def refresh_token():
    """Refreshes the Spotify access token every 55 minutes"""
    global ACCESS_TOKEN
    while True:
        print("[🔄] Refreshing Spotify Token...")
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            ACCESS_TOKEN = response.json()["access_token"]
            print(f"[✅] New Token: {ACCESS_TOKEN[:20]}...")
        else:
            print("[❌] Failed to refresh token:", response.json())
        await asyncio.sleep(3300)  # Refresh every 55 minutes (Spotify expires in 1 hour)

@app.get("/now-playing")
def get_now_playing():
    """Fetches the currently playing track from Spotify"""
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        album_art = data["item"]["album"]["images"][0]["url"]
        return JSONResponse({"album_art": album_art, "song": data["item"]["name"], "artist": data["item"]["artists"][0]["name"]})
    else:
        return JSONResponse({"error": "No song is currently playing"}, status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await websocket.accept()
    last_song = None
    while True:
        response = requests.get("http://127.0.0.1:8000/now-playing").json()
        if "song" in response and response["song"] != last_song:
            await websocket.send_json(response)
            last_song = response["song"]
        await asyncio.sleep(5)  # Check every 5 seconds

# Start token refresh loop
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(refresh_token())