from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .history_logger import HistoryLogger
from .models import Track
from .player import MpvError, MpvPlayer
from .queue_manager import QueueManager


@dataclass
class PlaybackService:
    """Coordinates queue state, history logging and mpv playback."""

    player: MpvPlayer
    queue: QueueManager
    history: HistoryLogger = field(default_factory=HistoryLogger)
    _watcher_started: bool = False
    _play_lock: threading.RLock = field(default_factory=threading.RLock)
    _last_error: str | None = None

    def _record_started_track(self, track: Track) -> None:
        """Write history after mpv successfully accepted a track."""
        self.history.log_played(track)
        self._save_queue_snapshot()

    def _save_queue_snapshot(self) -> None:
        """Write the current queue/current/next state to disk."""
        self.history.save_queue_snapshot(self.queue.snapshot())

    def play_now(self, track: Track) -> None:
        """Interrupt the current item and play a track immediately."""
        with self._play_lock:
            self.queue.set_current(track)
            self.player.play_now(track.url)
            self._last_error = None
            self._record_started_track(track)

    def enqueue(self, track: Track) -> None:
        """Add a track to the queue and autostart if nothing is playing."""
        self.queue.add(track)
        self._save_queue_snapshot()

        if self.queue.current() is None:
            self.play_next()

    def play_next(self) -> Track | None:
        """Play the next queued track. Stop mpv if the queue is empty."""
        with self._play_lock:
            next_track = self.queue.pop_next()
            self.queue.set_current(next_track)

            if next_track is None:
                try:
                    self.player.stop()
                except MpvError:
                    pass
                self._save_queue_snapshot()
                return None

            self.player.play_now(next_track.url)
            self._last_error = None
            self._record_started_track(next_track)
            return next_track

    def remove_from_queue(self, queue_id: str) -> bool:
        removed = self.queue.remove(queue_id) is not None
        self._save_queue_snapshot()
        return removed

    def clear_queue(self) -> None:
        self.queue.clear()
        self._save_queue_snapshot()

    def toggle_pause(self) -> None:
        self.player.toggle_pause()

    def set_volume(self, volume: int) -> None:
        self.player.set_volume(volume)

    def state(self) -> dict[str, object]:
        """Return everything the browser needs in one JSON object."""
        try:
            player_status = self.player.status()
        except MpvError as exc:
            player_status = {
                "running": False,
                "paused": True,
                "idle_active": True,
                "volume": None,
                "media_title": None,
            }
            self._last_error = str(exc)

        snapshot = self.queue.snapshot()
        return {
            "app": {
                "name": "JulesTube Premium",
                "stage": "Etappe 2.2",
                "last_error": self._last_error,
            },
            "player": player_status,
            **snapshot,
        }

    def start_watcher(self) -> None:
        """Start a small daemon thread that advances the queue when mpv is idle."""
        if self._watcher_started:
            return

        self._watcher_started = True
        thread = threading.Thread(target=self._watch_loop, daemon=True)
        thread.start()

    def _watch_loop(self) -> None:
        while True:
            time.sleep(1.0)
            current = self.queue.current()
            if current is None:
                continue

            try:
                status = self.player.status()
            except MpvError as exc:
                self._last_error = str(exc)
                continue

            if status.get("running") and status.get("idle_active"):
                try:
                    self.play_next()
                except MpvError as exc:
                    self._last_error = str(exc)
