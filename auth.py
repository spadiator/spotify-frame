import os
import json
import bcrypt
import requests
import random
import string
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from supabase import create_client

# Supabase Credentials
SUPABASE_URL = "https://lsbbqdhbhnxhosrrmqkn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzYmJxZGhiaG54aG9zcnJtcWtuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzcwNDY0ODYsImV4cCI6MjA1MjYyMjQ4Nn0.RJqYuXQAV5KJiC5_PNUPOQq_qukUlMF2NYm-osZK-PE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Spotify Credentials
SPOTIFY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIFY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"

app = Flask(__name__)
CORS(app)

# Helper function to generate pairing codes
def generate_pairing_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    response = supabase.table("users").insert({"email": email, "password": hashed_password}).execute()
    
    if hasattr(response, 'error') and response.error:
        return jsonify({"error": response.error}), 400

    return jsonify({"message": "Signup successful"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    response = supabase.table("users").select("*").eq("email", email).execute()
    
    if not response.data:
        return jsonify({"error": "Invalid credentials"}), 401

    user = response.data[0]

    if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "user_id": user["id"]}), 200

@app.route("/pair", methods=["POST"])
def pair():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    pairing_code = generate_pairing_code()

    response = supabase.table("devices").insert({"user_id": user_id, "pairing_code": pairing_code, "status": "pending"}).execute()

    if hasattr(response, 'error') and response.error:
        return jsonify({"error": response.error}), 400

    return jsonify({"pairing_code": pairing_code}), 201

@app.route("/authorize/<user_id>", methods=["GET"])
def authorize(user_id):
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={SPOTIFY_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={SPOTIFY_REDIRECT_URI}"
        f"&scope=user-read-playback-state%20user-read-currently-playing"
        f"&state={user_id}"
    )
    return redirect(auth_url)

@app.route("/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    user_id = request.args.get("state")

    if not code or not user_id:
        return jsonify({"error": "Missing code or user_id"}), 400

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_response = requests.post(token_url, data=payload, headers=headers)
    
    if token_response.status_code != 200:
        return jsonify({"error": "Failed to retrieve tokens"}), 400

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token or not refresh_token:
        return jsonify({"error": "Invalid response from Spotify"}), 400

    response = supabase.table("devices").update({
        "spotify_access_token": access_token,
        "spotify_refresh_token": refresh_token,
        "status": "paired"
    }).eq("user_id", user_id).execute()

    if hasattr(response, 'error') and response.error:
        return jsonify({"error": response.error}), 400

    return jsonify({"message": "Spotify linked successfully!"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)