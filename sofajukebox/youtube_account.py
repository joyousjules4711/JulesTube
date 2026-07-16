from __future__ import annotations

from typing import Any

from yt_dlp import YoutubeDL

from .playlist_loader import _entry_to_track


ACCOUNT_FEEDS: dict[str, dict[str, str]] = {
    "watch_later": {
        "title": "Später ansehen",
        "description": "Deine YouTube-Watch-Later-Liste",
        "url": ":ytwatchlater",
    },
    "liked": {
        "title": "Gefällt mir",
        "description": "Videos, die dir gefallen",
        "url": ":ytfav",
    },
    "history": {
        "title": "YouTube-Verlauf",
        "description": "Zuletzt auf YouTube abgespielte Videos",
        "url": ":ythistory",
    },
    "recommended": {
        "title": "Empfohlen",
        "description": "YouTube-Empfehlungen für deinen Account",
        "url": ":ytrec",
    },
}


def list_account_feeds() -> list[dict[str, str]]:
    return [
        {
            "id": feed_id,
            "title": feed["title"],
            "description": feed["description"],
        }
        for feed_id, feed in ACCOUNT_FEEDS.items()
    ]


def _extract_feed(url: str, limit: int) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "playlistend": limit,
        "noplaylist": False,
        "cookiesfrombrowser": ("firefox",),
    }

    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False) or {}


def load_account_feed_preview(feed_id: str, limit: int = 20) -> dict[str, Any]:
    clean_feed_id = str(feed_id or "").strip()

    if clean_feed_id not in ACCOUNT_FEEDS:
        raise ValueError("Unbekannte YouTube-Liste.")

    safe_limit = max(1, min(int(limit or 20), 100))
    feed = ACCOUNT_FEEDS[clean_feed_id]

    info = _extract_feed(feed["url"], safe_limit)

    entries = info.get("entries") or []
    tracks = []

    for entry in entries:
        if not entry:
            continue

        track = _entry_to_track(entry)

        if track.get("url"):
            tracks.append(track)

    return {
        "playlist": {
            "title": feed["title"],
            "channel": "YouTube Account",
            "source_url": feed["url"],
            "count": len(tracks),
            "feed_id": clean_feed_id,
        },
        "tracks": tracks[:safe_limit],
    }
