# SofaJukebox

SofaJukebox ist eine kleine lokale Web-App für Linux Mint: Du suchst YouTube-Videos am Smartphone und spielst sie auf dem Linux-PC über `mpv` ab.

Status: **Etappe 1** – lauffähiger Prototyp mit Suche, Warteschlange und Grundsteuerung.

## Funktionen in dieser Etappe

- YouTube-Suche über `yt-dlp`
- Wiedergabe über `mpv`
- Warteschlange per `mpv`-Playlist
- Play/Pause
- Nächster Titel
- Lautstärke setzen
- Bedienung im lokalen WLAN über Browser am Smartphone

## Installation auf Linux Mint

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mpv ffmpeg

cd sofa-jukebox
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Start

```bash
source .venv/bin/activate
python app.py
```

Dann am PC öffnen:

```text
http://127.0.0.1:5050
```

Vom Smartphone im gleichen WLAN:

```bash
hostname -I
```

Die erste IP-Adresse nehmen, zum Beispiel:

```text
http://192.168.178.42:5050
```

## Sicherheit

Diese Etappe ist nur für dein lokales WLAN gedacht. Es gibt noch kein Login und keine Nutzerverwaltung. Nicht ins Internet weiterleiten, nicht per Portfreigabe öffnen.

## Projektstruktur

```text
sofa-jukebox/
├── app.py
├── requirements.txt
└── sofajukebox/
    ├── __init__.py
    ├── player.py
    ├── routes.py
    ├── youtube.py
    ├── static/
    │   ├── app.js
    │   └── style.css
    └── templates/
        └── index.html
```

## Nächste Etappe

Etappe 2 wird die Warteschlange sauberer synchronisieren: aktueller Titel, bereits gespielte Titel ausblenden, Fehleranzeigen und automatische Status-Aktualisierung.
