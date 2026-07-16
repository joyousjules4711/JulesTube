from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLIENT_SECRET_FILE = PROJECT_ROOT / "client_secret.json"
TOKEN_FILE = PROJECT_ROOT / "data" / "youtube-token.json"
PUBLIC_URL_FILE = PROJECT_ROOT / "data" / "public-url.txt"


def get_public_url() -> str:
    url = PUBLIC_URL_FILE.read_text(encoding="utf-8").strip().rstrip("/")

    if not url.startswith("https://"):
        raise RuntimeError("Die JulesTube-Adresse muss HTTPS verwenden.")

    return url


def get_redirect_uri() -> str:
    return f"{get_public_url()}/auth/youtube/callback"


def create_flow(state: str | None = None) -> Flow:
    if not CLIENT_SECRET_FILE.exists():
        raise RuntimeError("client_secret.json wurde nicht gefunden.")

    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = get_redirect_uri()
    return flow


def save_credentials(credentials: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    TOKEN_FILE.chmod(0o600)


def delete_credentials() -> None:
    TOKEN_FILE.unlink(missing_ok=True)


def load_credentials() -> Credentials | None:
    if not TOKEN_FILE.exists():
        return None

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_credentials(credentials)

    return credentials if credentials.valid else None


def youtube_service():
    credentials = load_credentials()

    if credentials is None:
        raise PermissionError("YouTube ist nicht angemeldet.")

    return build(
        "youtube",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def list_my_playlists(limit: int = 50) -> list[dict]:
    """Load playlists owned by the connected YouTube account."""
    youtube = youtube_service()
    safe_limit = max(1, min(int(limit or 50), 200))

    playlists = []
    page_token = None

    while len(playlists) < safe_limit:
        response = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=min(50, safe_limit - len(playlists)),
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            details = item.get("contentDetails", {})
            thumbnails = snippet.get("thumbnails", {})

            thumbnail = (
                thumbnails.get("medium")
                or thumbnails.get("high")
                or thumbnails.get("default")
                or {}
            ).get("url")

            playlists.append(
                {
                    "id": item.get("id"),
                    "title": snippet.get("title") or "Unbenannte Playlist",
                    "description": snippet.get("description") or "",
                    "thumbnail": thumbnail,
                    "count": details.get("itemCount", 0),
                }
            )

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return playlists[:safe_limit]


def list_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
) -> list[dict]:
    """Load tracks from one playlist owned by the connected account."""
    youtube = youtube_service()
    safe_limit = max(1, min(int(limit or 100), 500))

    tracks = []
    page_token = None

    while len(tracks) < safe_limit:
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=min(50, safe_limit - len(tracks)),
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            details = item.get("contentDetails", {})
            resource = snippet.get("resourceId", {})

            video_id = (
                details.get("videoId")
                or resource.get("videoId")
            )

            if not video_id:
                continue

            thumbnails = snippet.get("thumbnails", {})

            thumbnail = (
                thumbnails.get("medium")
                or thumbnails.get("high")
                or thumbnails.get("default")
                or {}
            ).get("url")

            tracks.append(
                {
                    "id": video_id,
                    "video_id": video_id,
                    "title": snippet.get("title") or "Unbekanntes Video",
                    "channel": (
                        snippet.get("videoOwnerChannelTitle")
                        or snippet.get("channelTitle")
                        or ""
                    ),
                    "thumbnail": thumbnail,
                    "url": (
                        "https://www.youtube.com/watch"
                        f"?v={video_id}"
                    ),
                }
            )

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return tracks[:safe_limit]


def list_my_playlists(limit: int = 50) -> list[dict]:
    """Load playlists owned by the connected YouTube account."""
    youtube = youtube_service()
    safe_limit = max(1, min(int(limit or 50), 200))

    playlists = []
    page_token = None

    while len(playlists) < safe_limit:
        response = youtube.playlists().list(
            part="snippet,contentDetails",
            mine=True,
            maxResults=min(50, safe_limit - len(playlists)),
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            details = item.get("contentDetails", {})
            thumbnails = snippet.get("thumbnails", {})

            thumbnail = (
                thumbnails.get("medium")
                or thumbnails.get("high")
                or thumbnails.get("default")
                or {}
            ).get("url")

            playlists.append(
                {
                    "id": item.get("id"),
                    "title": snippet.get("title") or "Unbenannte Playlist",
                    "description": snippet.get("description") or "",
                    "thumbnail": thumbnail,
                    "count": details.get("itemCount", 0),
                }
            )

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return playlists[:safe_limit]


def list_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
) -> list[dict]:
    """Load tracks from one playlist owned by the connected account."""
    youtube = youtube_service()
    safe_limit = max(1, min(int(limit or 100), 500))

    tracks = []
    page_token = None

    while len(tracks) < safe_limit:
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=min(50, safe_limit - len(tracks)),
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            details = item.get("contentDetails", {})
            resource = snippet.get("resourceId", {})

            video_id = (
                details.get("videoId")
                or resource.get("videoId")
            )

            if not video_id:
                continue

            thumbnails = snippet.get("thumbnails", {})

            thumbnail = (
                thumbnails.get("medium")
                or thumbnails.get("high")
                or thumbnails.get("default")
                or {}
            ).get("url")

            tracks.append(
                {
                    "id": video_id,
                    "video_id": video_id,
                    "title": snippet.get("title") or "Unbekanntes Video",
                    "channel": (
                        snippet.get("videoOwnerChannelTitle")
                        or snippet.get("channelTitle")
                        or ""
                    ),
                    "thumbnail": thumbnail,
                    "url": (
                        "https://www.youtube.com/watch"
                        f"?v={video_id}"
                    ),
                }
            )

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return tracks[:safe_limit]


def get_account_profile() -> dict:
    """Return basic profile data for the connected YouTube channel."""
    youtube = youtube_service()

    response = youtube.channels().list(
        part="snippet",
        mine=True,
        maxResults=1,
    ).execute()

    items = response.get("items") or []

    if not items:
        return {
            "signed_in": True,
            "channel_title": "YouTube",
            "thumbnail": None,
        }

    snippet = items[0].get("snippet") or {}
    thumbnails = snippet.get("thumbnails") or {}

    thumbnail = (
        thumbnails.get("medium")
        or thumbnails.get("high")
        or thumbnails.get("default")
        or {}
    ).get("url")

    return {
        "signed_in": True,
        "channel_title": snippet.get("title") or "YouTube",
        "thumbnail": thumbnail,
    }
