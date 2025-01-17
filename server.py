import os
import uvicorn
import requests
import random
import string
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from fastapi.responses import RedirectResponse

# Spotify Credentials (unchanged)
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
SPOTIFY_REFRESH_TOKEN = "AQBPdyZ42yIk6HftPQLOkA8ehvKzXjEvkoPe9SnUILl_u_kC7tl7hDSLAAbiY5vTABdcBkZaqpdfUH-p8s4MyHCtBVNnPyg2-88srqu7nkVQ_3YAlWk7rgbTzc2rdz5rcwU"
SPOTIFY_REDIRECT_URI = "https://spotify-frame-1.onrender.com/callback"

# Supabase Setup
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

# Initialize FastAPI
app = FastAPI()

# Allow frontend access
origins = [
    "https://spotify-frame-1.onrender.com",
    "https://spotify-frame-dhso.onrender.com",
]

app = FastAPI(
    title="Spotify Frame API",
    description="API for retrieving and displaying currently playing Spotify album art.",
    version="1.0.0",
    docs_url="/docs",   # Ensure the API docs are enabled at /docs
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Ensure the frontend can call the API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test Root Endpoint
@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/spotify-auth")
def get_spotify_auth(pairing_code: str):
    auth_url = f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri=https://spotify-frame-dhso.onrender.com/callback&scope=user-read-playback-state user-read-currently-playing&state={pairing_code}"
    return RedirectResponse(auth_url)


@app.get("/callback")
def spotify_callback(code: str, state: str):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://spotify-frame-dhso.onrender.com/callback",  # Must match exactly
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)

    if response.status_code == 200:
        access_token = response.json().get("access_token")
        print(f"DEBUG: Retrieved Spotify Token - {access_token}")  # Debugging print statement

        if not access_token:
            print("ERROR: No access token received from Spotify.")
            raise HTTPException(status_code=400, detail="Failed to retrieve Spotify token")

        # Store access token in Supabase
        update_response = supabase.table("users").update({"spotify_token": access_token}).eq("pairing_code", state).execute()
        print(f"DEBUG: Supabase Update Response - {update_response}")  # Debugging print statement

        return {"message": "Spotify authorization successful"}
    else:
        print(f"ERROR: Spotify token request failed - {response.text}")
        raise HTTPException(status_code=400, detail="Spotify authorization failed")






class SignupRequest(BaseModel):
    email: str

def generate_pairing_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.post("/signup")
def signup(request: SignupRequest):
    email = request.email
    pairing_code = generate_pairing_code()

    try:
        response = supabase.table("users").insert({
            "email": email,
            "pairing_code": pairing_code,
            "spotify_token": None
        }).execute()
        
        return {"message": "User registered successfully!", "pairing_code": pairing_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving user data: {str(e)}")



# Spotify API URL
SPOTIFY_API_URL = "https://api.spotify.com/v1/me/player/currently-playing"



# Generate Unique Pairing Code
def generate_pairing_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

from pydantic import BaseModel

class SignupRequest(BaseModel):
    email: str

# ✅ **FIXED: Properly Handles JSON Input & Returns JSON**
@app.post("/signup")
def signup(email: str = Form(...)):
    pairing_code = generate_pairing_code()
    print(f"Attempting to insert user: {email} with pairing code {pairing_code}")  # Debugging print

    # Store in Supabase
    try:
        response = supabase.table("users").insert({
            "email": email,
            "pairing_code": pairing_code,
            "spotify_token": None
        }).execute()

        print("Supabase response:", response)  # Debugging print

        if "error" in response and response["error"]:
            print("Supabase Insert Error:", response["error"])
            raise HTTPException(status_code=500, detail=f"Supabase Error: {response['error']['message']}")

        return {"message": "User registered", "pairing_code": pairing_code}

    except Exception as e:
        print("Supabase Exception:", str(e))  # Debugging print
        raise HTTPException(status_code=500, detail=f"Error saving user data: {str(e)}")



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
        return response.json().get("access_token")
    return None

@app.get("/currently-playing")
def get_current_song():
    access_token = refresh_spotify_token()
    if not access_token:
        return {"error": "Failed to refresh token"}

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if response.status_code == 200:
        data = response.json()
        song_name = data["item"]["name"]
        album_art = data["item"]["album"]["images"][0]["url"]
        return {"song": song_name, "album_art": album_art}
    else:
        return {"error": "No song currently playing"}

# 🔥 Ensure FastAPI runs on Render's dynamically assigned port
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use Render's assigned port, fallback to 8000 locally
    uvicorn.run(app, host="0.0.0.0", port=port)