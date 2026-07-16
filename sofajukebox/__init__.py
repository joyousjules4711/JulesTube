from __future__ import annotations

from .playlist_routes import register_playlist_routes
from .youtube_account_routes import register_youtube_account_routes
from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .history_logger import HistoryLogger
from .player import MpvPlayer
from .playback import PlaybackService
from .queue_manager import QueueManager
from .routes import create_routes
from .youtube import YouTubeSearch


def create_app() -> Flask:
    """Create and configure the JulesTube Premium Flask application."""
    app = Flask(__name__)

    project_root = Path(app.root_path).parent
    secret_file = project_root / "data" / "flask-secret.txt"

    if not secret_file.exists():
        raise RuntimeError(
            "Flask-Session-Geheimnis fehlt: data/flask-secret.txt"
        )

    # JulesTube läuft hinter Tailscale Serve.
    # ProxyFix übernimmt das externe HTTPS-Protokoll und den Hostnamen.
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
    )

    app.secret_key = secret_file.read_text(
        encoding="utf-8"
    ).strip()

    player = MpvPlayer(socket_path="/tmp/julestube-premium-mpv.sock")
    queue = QueueManager()
    youtube = YouTubeSearch(max_results=20)

    data_dir = Path(app.root_path).parent / "data"
    history = HistoryLogger(data_dir=data_dir)
    playback = PlaybackService(player=player, queue=queue, history=history)
    playback.start_watcher()

    create_routes(app, playback=playback, youtube=youtube)
    register_playlist_routes(app)
    register_youtube_account_routes(app)
    return app