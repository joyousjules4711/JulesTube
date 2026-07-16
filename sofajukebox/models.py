from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Track:
    """One playable YouTube item."""

    title: str
    url: str
    channel: str = ""
    duration: str = ""
    video_id: str = ""
    thumbnail: str = ""
    added_by: str = ""
    queue_id: str = field(default_factory=lambda: uuid4().hex)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Track":
        """Build a Track from browser/API JSON payload."""
        if not isinstance(payload, dict):
            raise ValueError("Ungültige Track-Daten.")

        title = _clean_string(payload.get("title") or payload.get("name"))
        url = _clean_string(
            payload.get("url")
            or payload.get("webpage_url")
            or payload.get("original_url")
            or payload.get("link")
        )
        video_id = _clean_string(payload.get("video_id") or payload.get("id"))

        if not url and video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"

        if url and not url.startswith(("http://", "https://")):
            if not video_id:
                video_id = url
            url = f"https://www.youtube.com/watch?v={url}"

        if not url:
            raise ValueError("url fehlt.")

        if not title:
            title = "Unbekannter Titel"

        return cls(
            title=title,
            url=url,
            channel=_clean_string(payload.get("channel") or payload.get("uploader")),
            duration=_clean_string(payload.get("duration") or payload.get("duration_string")),
            video_id=video_id,
            thumbnail=_clean_thumbnail(payload.get("thumbnail") or payload.get("thumbnails")),
            added_by=_clean_string(payload.get("added_by") or payload.get("addedBy")),
            queue_id=_clean_string(payload.get("queue_id")) or uuid4().hex,
        )


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_thumbnail(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list) and value:
        last = value[-1]
        if isinstance(last, dict):
            return _clean_string(last.get("url"))

    if isinstance(value, dict):
        return _clean_string(value.get("url"))

    return ""
