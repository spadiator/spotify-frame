import os
import uvicorn
import requests
import random
import string
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# Initialize FastAPI
app = FastAPI()

# Allow frontend access
origins = [
    "https://spotify-frame-1.onrender.com",
    "https://spotify-frame-dhso.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Setup
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Spotify Credentials
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
SPOTIFY_REDIRECT_URI = "https://spotify-frame-1.onrender.com/callback"

# Generate Unique Pairing Code
def generate_pairing_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Signup Endpoint
@app.post("/signup")
def signup(email: str):
    pairing_code = generate_pairing_code()

    # Store in Supabase
    data, count = supabase.table("users").insert({
        "email": email,
        "pairing_code": pairing_code,
        "spotify_token": None
    }).execute()

    if not data:
        raise HTTPException(status_code=500, detail="Error saving user data")

    return {"message": "User registered", "pairing_code": pairing_code}

# Spotify Authorization URL
@app.get("/spotify-auth")
def get_spotify_auth(pairing_code: str):
    auth_url = f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={SPOTIFY_REDIRECT_URI}&scope=user-read-playback-state user-read-currently-playing&state={pairing_code}"
    return {"auth_url": auth_url}

# Callback for Spotify OAuth
@app.get("/callback")
def spotify_callback(code: str, state: str):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)

    if response.status_code == 200:
        access_token = response.json().get("access_token")

        # Store access token in Supabase
        supabase.table("users").update({"spotify_token": access_token}).eq("pairing_code", state).execute()

        return {"message": "Spotify authorized successfully"}
    else:
        raise HTTPException(status_code=400, detail="Spotify authorization failed")

# ✅ Add the currently-playing endpoint
@app.get("/currently-playing")
def get_current_song():
    # Fetch the most recent user token from Supabase
    data = supabase.table("users").select("spotify_token").order("created_at", desc=True).limit(1).execute()
    if not data or not data[1] or not data[1][0]["spotify_token"]:
        raise HTTPException(status_code=400, detail="No Spotify token found")

    access_token = data[1][0]["spotify_token"]
    SPOTIFY_API_URL = "https://api.spotify.com/v1/me/player/currently-playing"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SPOTIFY_API_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "item" in data:
            song_name = data["item"]["name"]
            album_art = data["item"]["album"]["images"][0]["url"]
            return {"song": song_name, "album_art": album_art}
    return {"error": "No song currently playing"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)