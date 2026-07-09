# JulesTube - Your couch. Your music. Your rules.

JulesTube is a lightweight web-based remote control for YouTube on Linux.  Search for videos from your phone, add them to the queue, and play them instantly on your Linux PC using mpv and YouTube Premium. No Chromecast required.  Designed as a fun weekend project that grew into a personal music hub.

✨ Features (planned)

🔍 Search YouTube from any device in your local network

🎵 Play videos on a Linux PC with mpv

📃 Shared queue

⏯️ Play / Pause / Skip

🔊 Volume control

❤️ Favorites

🌙 Sleep timer

📱 Installable as a Progressive Web App (PWA)

👥 Multi-user party mode

🎙️ Optional Alexa integration

🛠️ Tech Stack

Python
FastAPI
mpv
yt-dlp
HTML / CSS / JavaScript
SQLite


🎼 Roadmap
Version	Codename
0.1	Prelude
0.2	Overture
0.3	Crescendo
0.4	Harmony
0.5	Nocturne
1.0	Encore
Philosophy

JulesTube isn't trying to replace YouTube.

It's about creating a simple, elegant way to control playback on a Linux PC from your phone while keeping everything inside your own home network.

No cloud.
No subscriptions.
No unnecessary complexity.

Just music.

## 🚀 Development

### Virtuelle Umgebung aktivieren

```bash
source .venv/bin/activate
```

### Server starten

```bash
uvicorn app:app --reload
```

### Server beenden

```bash
fuser -k 8000/tcp
```

### Git Status

```bash
git status
```

### Commit

```bash
git add .
git commit -m "..."
git push
```
