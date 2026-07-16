from __future__ import annotations

from flask import jsonify, redirect, request, session

from .youtube_account import list_account_feeds, load_account_feed_preview
from .youtube_oauth import (
    create_flow,
    delete_credentials,
    get_account_profile,
    get_public_url,
    list_my_playlists,
    list_playlist_tracks,
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
            session["youtube_code_verifier"] = flow.code_verifier
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
            flow.code_verifier = session.get(
                "youtube_code_verifier"
            )

            callback_url = (
                f"{get_public_url()}/auth/youtube/callback"
                f"?{request.query_string.decode('utf-8')}"
            )

            flow.fetch_token(
                authorization_response=callback_url
            )
            save_credentials(flow.credentials)

        except Exception as error:
            app.logger.exception(
                "YouTube-Anmeldung ist fehlgeschlagen."
            )
            return f"YouTube-Anmeldung fehlgeschlagen: {error}", 500

        finally:
            session.pop("youtube_oauth_state", None)
            session.pop("youtube_code_verifier", None)

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

    @app.get("/api/youtube/my-playlists")
    def api_youtube_my_playlists():
        limit = request.args.get("limit", 50)

        try:
            playlists = list_my_playlists(
                limit=int(limit)
            )
            return jsonify({
                "playlists": playlists,
            })

        except PermissionError as error:
            return jsonify({
                "signed_in": False,
                "error": str(error),
            }), 401

        except Exception as error:
            app.logger.exception(
                "YouTube-Playlists konnten nicht geladen werden."
            )
            return jsonify({
                "error": (
                    "Playlists konnten nicht geladen werden: "
                    f"{error}"
                ),
            }), 502

    @app.get("/api/youtube/my-playlist/<playlist_id>")
    def api_youtube_my_playlist(playlist_id: str):
        limit = request.args.get("limit", 100)

        try:
            tracks = list_playlist_tracks(
                playlist_id=playlist_id,
                limit=int(limit),
            )

            return jsonify({
                "playlist_id": playlist_id,
                "count": len(tracks),
                "tracks": tracks,
            })

        except PermissionError as error:
            return jsonify({
                "signed_in": False,
                "error": str(error),
            }), 401

        except Exception as error:
            app.logger.exception(
                "YouTube-Playlist konnte nicht geladen werden."
            )
            return jsonify({
                "error": (
                    "Playlist konnte nicht geladen werden: "
                    f"{error}"
                ),
            }), 502

    @app.get("/api/youtube/account/status")
    def api_youtube_account_status():
        try:
            profile = get_account_profile()

            return jsonify({
                **profile,
                "login_url": "/auth/youtube/login",
                "logout_url": "/auth/youtube/logout",
            })

        except PermissionError:
            return jsonify({
                "signed_in": False,
                "channel_title": None,
                "thumbnail": None,
                "login_url": "/auth/youtube/login",
                "logout_url": "/auth/youtube/logout",
            })

        except Exception as error:
            app.logger.exception(
                "YouTube-Kontoprofil konnte nicht geladen werden."
            )

            return jsonify({
                "signed_in": False,
                "error": str(error),
                "login_url": "/auth/youtube/login",
            }), 502

