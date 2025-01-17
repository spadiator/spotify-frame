from flask import Flask, request, jsonify, redirect, render_template
import sqlite3
import qrcode
import os
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
SPOTIPY_CLIENT_ID = "fa74ddfa85064b4a9cd807d1b596e3d6"
SPOTIPY_CLIENT_SECRET = "09e10109bd5d42e493d7751f37d409fc"
SPOTIPY_REDIRECT_URI = "https://ba3a-2605-a601-a0d3-3900-8c75-9fc3-bfb1-a928.ngrok-free.app/callback"
SCOPE = "user-read-currently-playing user-read-playback-state"

# Database setup
DB_FILE = "spotify_devices.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE devices (device_id TEXT, token TEXT, refresh_token TEXT, expires_at INTEGER)")
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/authorize/<device_id>')
def authorize(device_id):
    """Generate QR code and Spotify authorization URL for a device."""
    conn = get_db_connection()
    conn.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
    conn.commit()
    conn.close()

    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI, scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url(state=device_id)

    # Generate QR code
    qr = qrcode.QRCode()
    qr.add_data(auth_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_path = f"static/qr_{device_id}.png"
    qr_img.save(qr_path)

    return render_template("qr_display.html", qr_path=qr_path)

@app.route('/callback')
def callback():
    """Handle Spotify authorization callback."""
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI, scope=SCOPE)
    code = request.args.get('code')
    state = request.args.get('state')
    token_info = sp_oauth.get_access_token(code)

    conn = get_db_connection()
    conn.execute("INSERT INTO devices (device_id, token, refresh_token, expires_at) VALUES (?, ?, ?, ?)",
                 (state, token_info['access_token'], token_info['refresh_token'], token_info['expires_at']))
    conn.commit()
    conn.close()

    return f"Device {state} authorized successfully! You can start playing music now."

@app.route('/playback/<device_id>')
def playback(device_id):
    """Get current playback for a device."""
    conn = get_db_connection()
    device = conn.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
    conn.close()

    if not device:
        return jsonify({"error": "Device not found"}), 404

    token = device["token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)

    if response.status_code == 401:
        return jsonify({"error": "Token expired"}), 401
    elif response.status_code == 204:
        return jsonify({"error": "No active playback"}), 204
    elif response.status_code != 200:
        return jsonify({"error": "An error occurred while fetching playback info"}), response.status_code

    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)