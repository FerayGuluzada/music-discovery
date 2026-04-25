import spotipy
import os
import json
import base64
import requests
import time 
from io import BytesIO
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    #scope="playlist-read-private playlist-read-collaborative"
    #scope="playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
    scope="playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public user-read-private"
))

# -------------------------
# FIND SHAZAM PLAYLIST
# -------------------------
playlists = sp.current_user_playlists()

shazam_playlist = None

for p in playlists['items']:
    if "shazam" in p['name'].lower():
        shazam_playlist = p
        break

if not shazam_playlist:
    raise Exception("Shazam playlist not found")

source_playlist_id = shazam_playlist['id']


# -------------------------
# ARTIST GENRE CACHE
# -------------------------
artist_cache = {}

def get_artist_genres(artist_id):
    if artist_id in artist_cache:
        return artist_cache[artist_id]

    artist = sp.artist(artist_id)
    genres = artist.get("genres", [])

    artist_cache[artist_id] = genres
    return genres


def extract_year(release_date):
    return int(release_date[:4]) if release_date else None


# -------------------------
# GET ALL TRACKS
# -------------------------
tracks = []
results = sp.playlist_items(source_playlist_id)

while results:
    for item in results['items']:
        track = item['track']

        if not track:
            continue

        artist = track["artists"][0]
        artist_id = artist["id"]

        release_date = track["album"]["release_date"]

        tracks.append({
            "id": track["id"],
            "name": track["name"],
            "artist": artist["name"],

            "genres": get_artist_genres(artist_id),

            "release_year": extract_year(release_date),

            "added_at": item["added_at"]
        })

    if results['next']:
        results = sp.next(results)
    else:
        results = None


# -------------------------
# SAVE TO FILE (LLM READY)
# -------------------------
output_file = "shazam_llm_ready.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(tracks, f, indent=2, ensure_ascii=False)

print(f"Saved {len(tracks)} tracks to {output_file}")




client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = f"""
You are a music curator with deep knowledge of genres, artist styles and listening patterns.

Your goal is to help people find songs matching a certain vibe.

Your task is to group songs into playlists based on musical similarities, listening experience and vibe.

You must use ONLY the provided songs.

You should consider the following signals:
1. General musical interpretation
3. Artist similarity
3. Genres (if available)
4. Release year (era grouping)


Important rules:
- Number of playlists should be between 3 and 7
- Playlist must have minimum 3 songs
- Every track must belong to EXACTLY one playlist, no duplicates allowed.

Ensure playlists are musically consistent internally and clearly distinct in genre, mood, or listening context.

Playlist names should feel like they come from a human music curator with taste, not a genre database.

Avoid generic industry labels like:
- "Modern Pop Hits"
- "Classic Rock"
- "Indie & Alternative"

Instead, prefer names that reflect listening experience, mood, or identity, such as:
- "Late Night Drive Pop"
- "Bedroom Indie Glow"
- "Rainy Day Rock Classics"
- "Soft Chaos R&B"

For each playlist also generate a cover_prompt.

cover_prompt should be a short visual description for AI image generation.
It should describe aesthetic Spotify cover art matching the playlist vibe.

Good examples:
- neon city street at midnight, purple glow, cinematic
- dreamy cloudy sky, soft pink haze, nostalgic film grain
- dark forest fog, moody shadows, minimalist album art
- golden sunset highway drive, warm tones, retro style

Do NOT include text in the image.
Do NOT mention artists or song names.

Output MUST be valid JSON only:

{{
  "playlists": [
    {{
      "name": "...",
      "description": "...",
      "cover_prompt": "...",
      "track_ids": ["..."]
    }}
  ]
}}



Here is the dataset:
{json.dumps(tracks, separators=(",", ":"))}
"""

response = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt
)

result_text = response.output_text

print(result_text)

import re
import json

def clean_json_response(text):
    text = text.strip()

    # remove markdown fences if present
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    return text.strip()


cleaned = clean_json_response(result_text)

playlists = json.loads(cleaned)

def dedupe(playlists):
    for p in playlists["playlists"]:
        seen = set()
        clean = []

        for tid in p["track_ids"]:
            if tid and tid not in seen:
                clean.append(tid)
                seen.add(tid)

        p["track_ids"] = clean

    return playlists


playlists = dedupe(playlists)

with open("playlists.json", "w", encoding="utf-8") as f:
    json.dump(playlists, f, indent=2)

print("Saved playlists.json")

# -------------------------
# LOAD GPT PLAYLISTS
# -------------------------
with open("playlists.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Get current user ID
user_id = sp.current_user()["id"]


# -------------------------------------------------
# IMAGE HELPERS
# -------------------------------------------------
DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

def generate_cover(prompt_text):
    url = "https://api.deepinfra.com/v1/openai/images/generations"

    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt_text,
        "size": "1024x1024",
        "model": "black-forest-labs/FLUX-2-klein-4b",
        "n": 1
    }

    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    data = res.json()

    image_b64 = data["data"][0]["b64_json"]
    img_bytes = base64.b64decode(image_b64)

    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    img = img.resize((512, 512))

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=60, optimize=True)

    return buffer.getvalue()



def upload_cover(playlist_id, image_bytes):
    token = sp.auth_manager.get_cached_token()["access_token"]

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/images"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "image/jpeg"
    }

    res = requests.put(url, headers=headers, data=image_bytes)

    print("UPLOAD DEBUG:", res.status_code, res.text)

    if res.status_code not in [200, 202]:
        raise Exception(f"Upload failed: {res.status_code} {res.text}")
# -------------------------------------------------
# CREATE PLAYLISTS + SONGS + COVERS
# -------------------------------------------------

for playlist in playlists["playlists"]:
    name = playlist["name"]
    description = playlist["description"]
    track_ids = playlist["track_ids"]
    cover_prompt = playlist["cover_prompt"]

    # create playlist
    created = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description
    )

    created_playlist_id = created["id"]

    # print("USER ID:", sp.current_user()["id"])
    # print("PLAYLIST OWNER:", created["owner"]["id"])
    # print("PLAYLIST ID:", created_playlist_id)

    # add tracks
    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(
            created_playlist_id,
            track_ids[i:i+100]
        )

    print(f"Created playlist: {name}")

# COVER GENERATION DISABLED (keep prompt for future use)
# cover_prompt is stored in JSON and can be used later for image generation

    # try:
    #     img_bytes = generate_cover(cover_prompt)
    #     upload_cover(created_playlist_id, img_bytes)
    #     print("Uploaded cover")
    #     time.sleep(1.5)
    # except Exception as e:
    #     print("Cover failed:", e)
    #     time.sleep(2)