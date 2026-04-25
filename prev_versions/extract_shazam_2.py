import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="playlist-modify-private playlist-modify-public"
))

# -------------------------
# GET USER ID
# -------------------------
user_id = sp.current_user()["id"]

# -------------------------
# TEST TRACK IDS (replace with yours)
# -------------------------
track_ids = [
    "6QTPacyXkZWG9FMwq6L1hJ",
    "3MUFebos5drIwrUHxUorhP"
]

# -------------------------
# CREATE PLAYLIST
# -------------------------
playlist = sp.user_playlist_create(
    user=user_id,
    name="Test AI Playlist",
    public=False,
    description="Testing Spotify API playlist creation"
)

playlist_id = playlist["id"]

print("Created playlist:", playlist["name"])

# -------------------------
# ADD TRACKS
# -------------------------
sp.playlist_add_items(
    playlist_id=playlist_id,
    items=track_ids
)

print("Added tracks:", track_ids)
print("Done.")