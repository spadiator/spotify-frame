import requests
import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
import time

# Constants
DEVICE_ID = "12345"  # Replace with your device ID
ENDPOINT = f"http://127.0.0.1:5000/playback/{DEVICE_ID}"  # Flask endpoint
POLL_INTERVAL = 5  # Polling interval in seconds

# Initialize tkinter window
root = tk.Tk()
root.title("Spotify Album Art")
root.geometry("800x800")  # Adjust for your local testing
root.configure(background="black")

# Album art and metadata placeholders
album_art_label = tk.Label(root, bg="black")
album_art_label.pack(pady=20)
metadata_label = tk.Label(root, bg="black", fg="white", font=("Bebas Neue", 24))
metadata_label.pack()

def fetch_and_update():
    try:
        # Fetch playback data
        response = requests.get(ENDPOINT)
        response.raise_for_status()
        data = response.json()

        # Check if playback data is available
        if "error" in data:
            metadata_label.config(text="No playback data available")
            return

        # Extract relevant info
        track_name = data["item"]["name"]
        artist_name = data["item"]["artists"][0]["name"]
        album_name = data["item"]["album"]["name"]
        album_art_url = data["item"]["album"]["images"][0]["url"]
        is_playing = data["is_playing"]

        # Update metadata display
        status = "Playing" if is_playing else "Paused"
        metadata = f"{track_name}\n{artist_name}\n{album_name}\n[{status}]"
        metadata_label.config(text=metadata)

        # Fetch and display album art
        art_response = requests.get(album_art_url)
        art_image = Image.open(BytesIO(art_response.content))
        art_image = art_image.resize((600, 600))
        album_art = ImageTk.PhotoImage(art_image)
        album_art_label.config(image=album_art)
        album_art_label.image = album_art

    except Exception as e:
        metadata_label.config(text=f"Error fetching playback data: {e}")

    # Schedule the next update
    root.after(POLL_INTERVAL * 1000, fetch_and_update)

# Start the polling and tkinter main loop
fetch_and_update()
root.mainloop()