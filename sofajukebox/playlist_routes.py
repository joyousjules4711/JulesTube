from __future__ import annotations

from flask import jsonify, request

from .playlist_loader import load_playlist_preview


def register_playlist_routes(app):
    @app.route("/api/playlist/preview", methods=["POST"])
    def api_playlist_preview():
        payload = request.get_json(silent=True) or {}

        url = payload.get("url") or ""
        limit = payload.get("limit") or 20

        try:
            data = load_playlist_preview(url, limit=limit)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except Exception as error:
            return jsonify({
                "error": f"Playlist konnte nicht geladen werden: {error}"
            }), 502

        return jsonify(data)
