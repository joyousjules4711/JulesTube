from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL


def _format_duration(seconds: Any) -> str:
    if seconds in (None, ""):
        return ""

    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return ""

    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"


def _looks_like_youtube_playlist_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()

    if not host:
        return False

    is_youtube = (
        "youtube.com" in host
        or "youtu.be" in host
        or "music.youtube.com" in host
    )

    if not is_youtube:
        return False

    query = parse_qs(parsed.query)
    return "list" in query or "/playlist" in parsed.path


def _entry_to_track(entry: dict[str, Any]) -> dict[str, str]:
    video_id = str(entry.get("id") or "").strip()

    url = (
        entry.get("webpage_url")
        or entry.get("url")
        or ""
    )

    if video_id and not str(url).startswith("http"):
        url = f"https://www.youtube.com/watch?v={video_id}"

    thumbnail = entry.get("thumbnail") or ""

    thumbnails = entry.get("thumbnails") or []
    if not thumbnail and thumbnails:
        thumbnail = thumbnails[-1].get("url", "")

    duration = (
        entry.get("duration_string")
        or entry.get("duration")
        or ""
    )

    if not isinstance(duration, str):
        duration = _format_duration(duration)

    return {
        "title": str(entry.get("title") or "Unbekannter Titel"),
        "url": str(url),
        "channel": str(entry.get("channel") or entry.get("uploader") or ""),
        "duration": str(duration),
        "video_id": video_id,
        "thumbnail": str(thumbnail or ""),
    }


def _extract_playlist(url: str, limit: int, use_cookies: bool) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "playlistend": limit,
        "noplaylist": False,
    }

    if use_cookies:
        options["cookiesfrombrowser"] = ("firefox",)

    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False) or {}


def load_playlist_preview(url: str, limit: int = 20) -> dict[str, Any]:
    clean_url = (url or "").strip()

    if not clean_url:
        raise ValueError("Bitte einen YouTube-Playlist-Link einfügen.")

    if not _looks_like_youtube_playlist_url(clean_url):
        raise ValueError("Das sieht nicht nach einem YouTube-Playlist-Link aus.")

    safe_limit = max(1, min(int(limit or 20), 100))

    try:
        info = _extract_playlist(clean_url, safe_limit, use_cookies=True)
    except Exception:
        info = _extract_playlist(clean_url, safe_limit, use_cookies=False)

    entries = info.get("entries") or []
    tracks = []

    for entry in entries:
        if not entry:
            continue

        track = _entry_to_track(entry)

        if track["url"]:
            tracks.append(track)

    playlist = {
        "title": str(info.get("title") or "YouTube Playlist"),
        "channel": str(info.get("channel") or info.get("uploader") or ""),
        "source_url": clean_url,
        "count": len(tracks),
    }

    return {
        "playlist": playlist,
        "tracks": tracks[:safe_limit],
    }
