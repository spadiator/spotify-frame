import requests
import time
import pygame
import sys
from io import BytesIO

# Supabase details
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"

# Spotify credentials
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"

# Get stored tokens from Supabase
def get_latest_tokens():
    url = f"{SUPABASE_URL}/rest/v1/devices"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200 and response.json():
        device = response.json()[-1]  # Get latest entry
        access_token = device.get("spotify_access_token")
        refresh_token = device.get("spotify_refresh_token")
        
        print(f"Retrieved Access Token: {access_token[:10]}...")  
        print(f"Retrieved Refresh Token: {refresh_token[:10]}..." if refresh_token else "No refresh token found!")

        return access_token, refresh_token

    print("Error: Could not fetch tokens from Supabase")
    return None, None

# Save new tokens to Supabase
def update_tokens(access_token, refresh_token):
    url = f"{SUPABASE_URL}/rest/v1/devices"
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "spotify_access_token": access_token,
        "spotify_refresh_token": refresh_token
    }
    response = requests.patch(url, json=data, headers=headers)
    print("Tokens updated in Supabase:", response.status_code)

# Refresh access token
def refresh_access_token(refresh_token):
    if not refresh_token:
        print("ERROR: No refresh token available. Exiting.")
        sys.exit(1)

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        new_token = response.json().get("access_token")
        print(f"New Access Token: {new_token[:10]}...")  
        update_tokens(new_token, refresh_token)
        return new_token
    else:
        print("Error refreshing token:", response.json())
        sys.exit(1)

# Fetch current track info from Spotify
def get_current_track(access_token):
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:  
        return "expired"
    elif response.status_code == 204:  
        print("No track currently playing.")
        return None
    else:
        print(f"Error fetching track info: {response.json()}")
        return None

# Display album art
def display_album_art(image_url):
    response = requests.get(image_url)
    img = pygame.image.load(BytesIO(response.content))

    screen.fill((0, 0, 0))
    img = pygame.transform.scale(img, (600, 600))
    screen.blit(img, (50, 50))
    pygame.display.flip()

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((700, 700))
pygame.display.set_caption("Spotify Album Art Display")

# Main loop
last_track_id = None
access_token, refresh_token = get_latest_tokens()

while True:
    track_data = get_current_track(access_token)

    if track_data == "expired":
        print("Access token expired. Refreshing...")
        access_token = refresh_access_token(refresh_token)
        continue  

    if track_data and "item" in track_data:
        track_id = track_data["item"]["id"]
        album_art_url = track_data["item"]["album"]["images"][0]["url"]

        if track_id != last_track_id:  
            display_album_art(album_art_url)
            last_track_id = track_id
            print(f"Updated album art for: {track_data['item']['name']} - {track_data['item']['artists'][0]['name']}")

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    time.sleep(5)  