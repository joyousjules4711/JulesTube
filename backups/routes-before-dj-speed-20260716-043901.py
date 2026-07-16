from __future__ import annotations

from collections import Counter

from io import BytesIO, StringIO

import csv
import json
from datetime import datetime

import qrcode

from flask import Flask, Response, jsonify, render_template, request, send_file

from .models import Track
from .network import join_url_from_request
from .player import MpvError
from .playback import PlaybackService
from .youtube import YouTubeSearch


def create_routes(app: Flask, playback: PlaybackService, youtube: YouTubeSearch) -> None:
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/search")
    def search():
        query = request.args.get("q", "")
        try:
            return jsonify({"results": youtube.search(query)})
        except Exception as exc:
            return jsonify({"error": f"YouTube-Suche fehlgeschlagen: {exc}"}), 502

    @app.get("/api/state")
    def state():
        return jsonify(playback.state())


    @app.get("/api/similar")
    def similar_videos():
        state = playback.state()
        current = state.get("current")

        if not current:
            return jsonify({"current": None, "results": []})

        title = (current.get("title") or "").strip()
        channel = (current.get("channel") or "").strip()
        current_video_id = (current.get("video_id") or "").strip()

        if not title:
            return jsonify({"current": current, "results": []})

        query = f"{title} {channel}".strip()

        try:
            results = youtube.search(query)
        except Exception as exc:
            return jsonify({"error": f"Ähnliche Videos konnten nicht geladen werden: {exc}"}), 502

        filtered = []
        for item in results:
            if current_video_id and item.get("video_id") == current_video_id:
                continue
            if item.get("url") == current.get("url"):
                continue
            filtered.append(item)

        return jsonify({
            "current": current,
            "query": query,
            "results": filtered[:20],
        })

    @app.get("/api/history")
    def history():
        raw_limit = request.args.get("limit", "30")
        try:
            limit = int(raw_limit)
        except ValueError:
            limit = 30

        limit = max(1, min(limit, 200))
        return jsonify({"history": playback.history.recent(limit)})


    @app.get("/api/history/day")
    def history_for_day():
        date_value = request.args.get("date", "").strip()

        try:
            items = playback.history.for_date(date_value)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        return jsonify({
            "date": date_value,
            "count": len(items),
            "history": items,
        })

    @app.get("/api/history/export.json")
    def history_export_json():
        date_value = request.args.get("date", "").strip()

        try:
            items = playback.history.for_date(date_value)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        payload = {
            "exported_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "date": date_value,
            "count": len(items),
            "history": items,
        }

        content = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )

        filename = f"julestube-abend-{date_value}.json"

        return Response(
            content,
            mimetype="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    @app.get("/api/history/export.csv")
    def history_export_csv():
        date_value = request.args.get("date", "").strip()

        try:
            items = playback.history.for_date(date_value)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        fieldnames = [
            "played_at",
            "title",
            "channel",
            "duration",
            "added_by",
            "url",
            "video_id",
            "thumbnail",
            "queue_id",
        ]

        buffer = StringIO()
        buffer.write("\ufeff")

        writer = csv.DictWriter(
            buffer,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()

        for item in items:
            writer.writerow({
                field: item.get(field, "")
                for field in fieldnames
            })

        filename = f"julestube-abend-{date_value}.csv"

        return Response(
            buffer.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{filename}"'
                )
            },
        )

    @app.get("/soundtrack")
    def soundtrack_page():
        return render_template("soundtrack.html")

    @app.get("/api/soundtrack")
    def soundtrack_data():
        date_value = request.args.get("date", "").strip()

        if not date_value:
            date_value = datetime.now().astimezone().date().isoformat()

        try:
            items = playback.history.for_date(date_value)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        def duration_seconds(value):
            if value is None:
                return 0

            if isinstance(value, (int, float)):
                return max(0, int(value))

            text_value = str(value).strip()

            if not text_value:
                return 0

            if text_value.isdigit():
                return int(text_value)

            try:
                parts = [int(part) for part in text_value.split(":")]
            except ValueError:
                return 0

            if len(parts) == 2:
                minutes, seconds = parts
                return minutes * 60 + seconds

            if len(parts) == 3:
                hours, minutes, seconds = parts
                return hours * 3600 + minutes * 60 + seconds

            return 0

        total_seconds = sum(
            duration_seconds(item.get("duration"))
            for item in items
        )

        dj_counter = Counter(
            str(item.get("added_by") or "").strip()
            for item in items
            if str(item.get("added_by") or "").strip()
        )

        channel_counter = Counter(
            str(item.get("channel") or "").strip()
            for item in items
            if str(item.get("channel") or "").strip()
        )

        song_counter = Counter(
            (
                str(item.get("video_id") or "").strip()
                or str(item.get("url") or "").strip()
                or str(item.get("title") or "").strip()
            )
            for item in items
        )

        item_by_song = {}

        for item in items:
            key = (
                str(item.get("video_id") or "").strip()
                or str(item.get("url") or "").strip()
                or str(item.get("title") or "").strip()
            )

            if key and key not in item_by_song:
                item_by_song[key] = item

        top_songs = []

        for key, count in song_counter.most_common(10):
            item = item_by_song.get(key, {})

            top_songs.append({
                "title": item.get("title") or "Unbekannter Titel",
                "channel": item.get("channel") or "",
                "thumbnail": item.get("thumbnail") or "",
                "url": item.get("url") or "",
                "count": count,
            })

        def counter_rows(counter, limit=5):
            return [
                {
                    "name": name,
                    "count": count,
                }
                for name, count in counter.most_common(limit)
            ]

        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60

        if hours:
            duration_label = f"{hours} Std. {minutes} Min."
        else:
            duration_label = f"{minutes} Min."

        return jsonify({
            "date": date_value,
            "song_count": len(items),
            "unique_song_count": len(song_counter),
            "total_seconds": total_seconds,
            "duration_label": duration_label,
            "first_song": items[0] if items else None,
            "last_song": items[-1] if items else None,
            "top_dj": (
                {
                    "name": dj_counter.most_common(1)[0][0],
                    "count": dj_counter.most_common(1)[0][1],
                }
                if dj_counter
                else None
            ),
            "top_channel": (
                {
                    "name": channel_counter.most_common(1)[0][0],
                    "count": channel_counter.most_common(1)[0][1],
                }
                if channel_counter
                else None
            ),
            "top_djs": counter_rows(dj_counter),
            "top_channels": counter_rows(channel_counter),
            "top_songs": top_songs,
        })

    @app.get("/api/join")
    def join_info():
        url = join_url_from_request(request.host)
        return jsonify({"join_url": url})

    @app.get("/join/qr.png")
    def join_qr():
        url = join_url_from_request(request.host)
        image = qrcode.make(url)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return send_file(buffer, mimetype="image/png", max_age=0)

    @app.get("/api/status")
    def status():
        return jsonify(playback.state())

    @app.post("/api/play")
    @app.post("/api/play-now")
    def play_now():
        body = request.get_json(force=True, silent=True) or {}
        try:
            track = Track.from_payload(body)
            playback.play_now(track)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except MpvError as exc:
            return jsonify({"error": str(exc)}), 500

        return jsonify({"ok": True, **playback.state()})

    @app.post("/api/queue/add")
    @app.post("/api/queue")
    def add_to_queue():
        body = request.get_json(force=True, silent=True) or {}
        try:
            track = Track.from_payload(body)
            playback.enqueue(track)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except MpvError as exc:
            return jsonify({"error": str(exc)}), 500

        return jsonify({"ok": True, **playback.state()})

    @app.delete("/api/queue/<queue_id>")
    def remove_from_queue(queue_id: str):
        removed = playback.remove_from_queue(queue_id)
        if not removed:
            return jsonify({"error": "Titel wurde nicht in der Queue gefunden."}), 404
        return jsonify({"ok": True, **playback.state()})

    @app.post("/api/queue/clear")
    def clear_queue():
        playback.clear_queue()
        return jsonify({"ok": True, **playback.state()})

    @app.post("/api/control/pause")
    def pause():
        try:
            playback.toggle_pause()
        except MpvError as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify({"ok": True, **playback.state()})

    @app.post("/api/control/next")
    def next_track():
        try:
            playback.play_next()
        except MpvError as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify({"ok": True, **playback.state()})

    @app.post("/api/control/volume")
    def volume():
        body = request.get_json(force=True, silent=True) or {}
        try:
            value = int(body.get("volume", 70))
            playback.set_volume(value)
        except (TypeError, ValueError):
            return jsonify({"error": "volume muss eine Zahl sein"}), 400
        except MpvError as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify({"ok": True, **playback.state()})
