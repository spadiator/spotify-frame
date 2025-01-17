import pygame
import requests
import time
from io import BytesIO

# Constants
PLAYBACK_URL = "https://ba3a-2605-a601-a0d3-3900-8c75-9fc3-bfb1-a928.ngrok-free.app/playback/808"  # Replace with your ngrok URL
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FONT_SIZE = 36
POLL_INTERVAL = 5  # Polling interval in seconds

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spotify Album Art Display")

# Load font
font = pygame.font.Font(None, FONT_SIZE)  # Use Pygame's default font

# Helper functions
def fetch_playback_data():
    """Fetch playback data from the Flask server."""
    try:
        response = requests.get(PLAYBACK_URL)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            return {"error": "No active playback"}
        else:
            print(f"Error fetching playback data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching playback data: {e}")
        return None

def download_album_art(url):
    """Download album art image from the URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pygame.image.load(BytesIO(response.content))
        else:
            print(f"Error downloading album art: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading album art: {e}")
        return None

def draw_display(album_art, track_name, artist_name):
    """Draw the album art and track information on the screen."""
    screen.fill((0, 0, 0))  # Clear screen with black background

    # Display blurred background
    if album_art:
        background = pygame.transform.scale(album_art, (SCREEN_WIDTH, SCREEN_HEIGHT))
        background.set_alpha(100)  # Add transparency
        screen.blit(background, (0, 0))

    # Display centered album art
    if album_art:
        album_art_scaled = pygame.transform.scale(album_art, (int(SCREEN_HEIGHT * 0.9), int(SCREEN_HEIGHT * 0.9)))
        album_rect = album_art_scaled.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(album_art_scaled, album_rect)

    # Render text
    if track_name and artist_name:
        track_surface = font.render(track_name, True, (255, 255, 255))
        artist_surface = font.render(artist_name, True, (200, 200, 200))
        track_rect = track_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        artist_rect = artist_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        screen.blit(track_surface, track_rect)
        screen.blit(artist_surface, artist_rect)

    pygame.display.flip()

# Main loop
def main():
    current_album_url = None
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        playback_data = fetch_playback_data()
        if playback_data and "error" not in playback_data:
            track_name = playback_data["item"]["name"]
            artist_name = playback_data["item"]["artists"][0]["name"]
            album_url = playback_data["item"]["album"]["images"][0]["url"]

            if album_url != current_album_url:  # Update only if the artwork changes
                album_art = download_album_art(album_url)
                current_album_url = album_url

            draw_display(album_art, track_name, artist_name)
        elif playback_data and playback_data.get("error") == "No active playback":
            print("No active playback. Waiting for updates...")
            draw_display(None, "No Active Playback", "")

        time.sleep(POLL_INTERVAL)

    pygame.quit()

# Run the script
if __name__ == "__main__":
    main()