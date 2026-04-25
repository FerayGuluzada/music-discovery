# 🎧 Music History → Listening Experiences

A small AI-powered system that turns my Shazam listening history into curated, vibe-based Spotify playlists.

Instead of treating music discovery as a flat list of songs, this project transforms it into meaningful listening experiences based on mood, context, and “feel”.

---

## 💡 Problem

I use Shazam a lot to capture songs I discover in daily life. Over time, this creates a large collection of music I genuinely like.

The problem is that this history is not usable in a meaningful way later.

- There is no structure beyond a long list of tracks  
- I can’t easily rediscover music based on mood or context  
- Going through hundreds of songs manually is unrealistic  

As a result, my music discovery ends at capture — not reuse.

---

## 🧠 Idea

This project uses AI to bridge the gap between raw music data and human listening experience.

Instead of relying only on low-level audio features (like tempo or danceability), it uses:

- Metadata (artist, genre, release year)  
- An LLM’s semantic understanding of music  

to group songs into meaningful vibe-based playlists.

---

## ⚙️ How It Works

### 1. Data Extraction

Pulls songs from a Shazam-linked Spotify playlist.

Uses Spotify API to collect metadata:

- Track name  
- Artist  
- Genres  
- Release year  
- Added date  

---

### 2. AI Processing

Sends the structured dataset to an LLM (ChatGPT).

The model groups songs into playlists based on:

- Vibe / mood  
- Listening context  
- Stylistic similarity  

Output is returned as structured JSON:

- Playlist name  
- Description  
- Track IDs  

---

### 3. Playlist Generation

A Python script reads the JSON output and:

- Automatically creates playlists in Spotify  
- Adds the correct tracks to each playlist  

---

## 🤖 How AI Is Used

AI is used in three main ways:

### Code Assistance

Helped build and iterate the Python pipeline and Spotify API integration.

### Prompt Engineering

Designed prompts that reliably transform raw song data into structured playlist outputs.

### Semantic Grouping Layer

Replaces low-level audio feature logic with higher-level interpretation of mood, vibe, and listening experience.

---

## 🎯 Result

The system turns a flat music history into curated playlists such as:

- **Late Night Soul Vulnerability**  
- **Neon Nights & Dance Floors**  
- **Early Morning Rides**  

---

## ⚠️ Limitations

- Spotify audio features (e.g. danceability, valence) were not used due to availability constraints  
- Playlist cover generation was implemented but disabled due to API upload limitations  
- Currently works as a batch system (not real-time)  

---

## 🔮 Future Improvements

- Time-based segmentation of listening history (e.g. “early discoveries” vs “recent taste”)  
- Continuous syncing when new songs are added  
- Integration with a social layer (see Tunebox project)  
- Automatic playlist evolution over time  
