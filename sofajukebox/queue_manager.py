from __future__ import annotations

from dataclasses import asdict, is_dataclass
from threading import RLock
from typing import Any

from .models import Track


class QueueManager:
    """Keeps current track and upcoming queue in memory."""

    def __init__(self) -> None:
        self._current: Track | None = None
        self._queue: list[Track] = []
        self._lock = RLock()

    def add(self, track: Track) -> None:
        with self._lock:
            self._queue.append(track)

    def pop_next(self) -> Track | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue.pop(0)

    def set_current(self, track: Track | None) -> None:
        with self._lock:
            self._current = track

    def current(self) -> Track | None:
        with self._lock:
            return self._current

    def next(self) -> Track | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def remove(self, queue_id: str) -> Track | None:
        with self._lock:
            for index, track in enumerate(self._queue):
                if getattr(track, "queue_id", "") == queue_id:
                    return self._queue.pop(index)
            return None

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "current": self._track_to_dict(self._current),
                "next": self._track_to_dict(self._queue[0]) if self._queue else None,
                "queue": [self._track_to_dict(track) for track in self._queue],
                "queue_length": len(self._queue),
            }

    def _track_to_dict(self, track: Track | None) -> dict[str, Any] | None:
        if track is None:
            return None

        if is_dataclass(track):
            return asdict(track)

        return {
            "title": getattr(track, "title", ""),
            "url": getattr(track, "url", ""),
            "channel": getattr(track, "channel", ""),
            "duration": getattr(track, "duration", ""),
            "video_id": getattr(track, "video_id", ""),
            "thumbnail": getattr(track, "thumbnail", ""),
            "queue_id": getattr(track, "queue_id", ""),
        }
