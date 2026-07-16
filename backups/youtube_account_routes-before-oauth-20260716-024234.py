from __future__ import annotations

from flask import jsonify, request

from .youtube_account import list_account_feeds, load_account_feed_preview


def register_youtube_account_routes(app):
    @app.get("/api/youtube/account-feeds")
    def api_youtube_account_feeds():
        return jsonify({
            "feeds": list_account_feeds(),
        })

    @app.post("/api/youtube/account-feed/preview")
    def api_youtube_account_feed_preview():
        payload = request.get_json(silent=True) or {}

        feed_id = payload.get("feed_id") or ""
        limit = payload.get("limit") or 20

        try:
            data = load_account_feed_preview(feed_id, limit=limit)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except Exception as error:
            return jsonify({
                "error": f"YouTube-Liste konnte nicht geladen werden: {error}"
            }), 502

        return jsonify(data)
