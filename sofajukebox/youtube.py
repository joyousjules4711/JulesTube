from __future__ import annotations

from typing import Any

import yt_dlp


class YouTubeSearch:
    """Small wrapper around yt-dlp's YouTube search."""

    def __init__(self, max_results: int = 10) -> None:
        self.max_results = max_results

    def search(self, query: str) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        search_query = f"ytsearch{self.max_results}:{query}"

        options = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(search_query, download=False)

        entries = info.get("entries", []) if isinstance(info, dict) else []

        results: list[dict[str, Any]] = []
        for entry in entries:
            if not entry:
                continue

            video_id = str(entry.get("id") or "").strip()
            url = str(entry.get("url") or "").strip()

            if video_id:
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
            elif url.startswith("http"):
                watch_url = url
            elif url:
                watch_url = f"https://www.youtube.com/watch?v={url}"
            else:
                continue

            thumbnail = self._thumbnail_for(entry, video_id)

            results.append(
                {
                    "title": entry.get("title") or "Unbekannter Titel",
                    "url": watch_url,
                    "video_id": video_id,
                    "channel": entry.get("channel") or entry.get("uploader") or "",
                    "duration": entry.get("duration_string") or self._format_duration(entry.get("duration")),
                    "thumbnail": thumbnail,
                }
            )

        return results

    def _thumbnail_for(self, entry: dict[str, Any], video_id: str) -> str:
        thumbnail = entry.get("thumbnail")
        if isinstance(thumbnail, str) and thumbnail.strip():
            return thumbnail.strip()

        thumbnails = entry.get("thumbnails")
        if isinstance(thumbnails, list) and thumbnails:
            for item in reversed(thumbnails):
                if isinstance(item, dict) and item.get("url"):
                    return str(item["url"]).strip()

        if video_id:
            return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        return ""

    def _format_duration(self, value: Any) -> str:
        if value is None:
            return ""

        try:
            total = int(value)
        except (TypeError, ValueError):
            return str(value)

        minutes, seconds = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)

        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"

        return f"{minutes}:{seconds:02d}"
