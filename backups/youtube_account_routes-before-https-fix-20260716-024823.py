from __future__ import annotations

from flask import jsonify, redirect, request, session

from .youtube_account import list_account_feeds, load_account_feed_preview
from .youtube_oauth import (
    create_flow,
    delete_credentials,
    get_public_url,
    save_credentials,
)


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

    @app.get("/auth/youtube/login")
    def youtube_login():
        try:
            flow = create_flow()

            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )

            session["youtube_oauth_state"] = state
            return redirect(authorization_url)

        except Exception as error:
            app.logger.exception(
                "YouTube-Login konnte nicht gestartet werden."
            )
            return (
                f"YouTube-Login konnte nicht gestartet werden: {error}",
                500,
            )

    @app.get("/auth/youtube/callback")
    def youtube_callback():
        expected_state = session.get("youtube_oauth_state")
        returned_state = request.args.get("state")

        if not expected_state or returned_state != expected_state:
            return (
                "Ungültiger OAuth-Status. "
                "Bitte die Anmeldung erneut starten.",
                400,
            )

        if request.args.get("error"):
            session.pop("youtube_oauth_state", None)
            return redirect(
                f"{get_public_url()}/?youtube=cancelled"
            )

        try:
            flow = create_flow(state=expected_state)
            flow.fetch_token(
                authorization_response=request.url
            )
            save_credentials(flow.credentials)

        except Exception as error:
            app.logger.exception(
                "YouTube-Anmeldung ist fehlgeschlagen."
            )
            return f"YouTube-Anmeldung fehlgeschlagen: {error}", 500

        finally:
            session.pop("youtube_oauth_state", None)

        return redirect(
            f"{get_public_url()}/?youtube=connected"
        )

    @app.get("/auth/youtube/logout")
    def youtube_logout():
        delete_credentials()
        session.pop("youtube_oauth_state", None)

        return redirect(
            f"{get_public_url()}/?youtube=logged-out"
        )

