from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any

from sofajukebox.models import Track


class HistoryLogger:
    """Writes played tracks and queue snapshots to local files."""

    def __init__(self, data_dir: str | Path = "data") -> None:
        self.data_dir = Path(data_dir)
        self.history_jsonl_path = self.data_dir / "history.jsonl"
        self.history_csv_path = self.data_dir / "history.csv"
        self.queue_snapshot_path = self.data_dir / "queue_snapshot.json"
        self._lock = RLock()

    def log_played(self, track: Track) -> None:
        """Append one started track to history.jsonl and history.csv."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        row = {
            "played_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "title": track.title,
            "url": track.url,
            "channel": track.channel,
            "duration": track.duration,
            "video_id": track.video_id,
            "thumbnail": track.thumbnail,
            "added_by": getattr(track, "added_by", ""),
            "queue_id": track.queue_id,
        }

        with self._lock:
            with self.history_jsonl_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

            csv_exists = self.history_csv_path.exists() and self.history_csv_path.stat().st_size > 0
            with self.history_csv_path.open("a", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(row.keys()))
                if not csv_exists:
                    writer.writeheader()
                writer.writerow(row)

    def save_queue_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Save current queue state as one readable JSON file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "saved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            **snapshot,
        }

        with self._lock:
            temp_path = self.queue_snapshot_path.with_suffix(".tmp")
            temp_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_path.replace(self.queue_snapshot_path)

    def recent(self, limit: int = 30) -> list[dict[str, Any]]:
        """Return the latest played tracks, newest last."""
        if not self.history_jsonl_path.exists():
            return []

        lines = self.history_jsonl_path.read_text(encoding="utf-8").splitlines()
        recent_lines = lines[-max(1, limit):]

        items: list[dict[str, Any]] = []
        for line in recent_lines:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return items

    def all_items(self) -> list[dict[str, Any]]:
        """Return all valid history entries in chronological order."""
        if not self.history_jsonl_path.exists():
            return []

        items: list[dict[str, Any]] = []

        with self._lock:
            lines = self.history_jsonl_path.read_text(
                encoding="utf-8"
            ).splitlines()

        for line in lines:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(item, dict):
                items.append(item)

        return items

    def for_date(self, date_value: str) -> list[dict[str, Any]]:
        """Return history entries whose local played_at date matches YYYY-MM-DD."""
        clean_date = str(date_value or "").strip()

        try:
            target_date = datetime.strptime(
                clean_date,
                "%Y-%m-%d",
            ).date()
        except ValueError as error:
            raise ValueError(
                "Datum muss im Format YYYY-MM-DD angegeben werden."
            ) from error

        matches: list[dict[str, Any]] = []

        for item in self.all_items():
            played_at = str(item.get("played_at") or "").strip()

            if not played_at:
                continue

            try:
                played_date = datetime.fromisoformat(
                    played_at
                ).date()
            except ValueError:
                continue

            if played_date == target_date:
                matches.append(item)

        return matches

