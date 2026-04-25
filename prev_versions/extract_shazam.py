import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="playlist-read-private playlist-read-collaborative"
))

# Step 1: find your Shazam playlist
playlists = sp.current_user_playlists()

shazam_playlist = None

for p in playlists['items']:
    if "shazam" in p['name'].lower():
        shazam_playlist = p
        break

if not shazam_playlist:
    raise Exception("Shazam playlist not found")

playlist_id = shazam_playlist['id']

# Step 2: extract tracks
tracks = []
results = sp.playlist_items(playlist_id)

for item in results['items']:
    track = item['track']
    tracks.append({
        "name": track["name"],
        "artist": track["artists"][0]["name"],
        "added_at": item["added_at"]
    })

print(tracks[:10])
