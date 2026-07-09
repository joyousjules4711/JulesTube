import json
import socket
import subprocess
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

MPV_SOCKET = "/tmp/julestube-mpv.sock"

app = FastAPI(
    title="JulesTube",
    description="Your couch. Your music. Your rules.",
    version="Emerald",
)

templates = Jinja2Templates(directory="templates")

current_player = None
current_video = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_home(request)


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str):
    videos = search_youtube(q)
    return render_home(request, query=q, videos=videos)


@app.get("/play/{video_id}", response_class=HTMLResponse)
def start_video(video_id):
    global current_player

    stop_player()
    remove_old_socket()

    url = f"https://www.youtube.com/watch?v={video_id}"

    current_player = subprocess.Popen(
        [
            "mpv",
            "--fullscreen",
            "--force-window=yes",
            f"--input-ipc-server={MPV_SOCKET}",
            "--ytdl-raw-options=cookies-from-browser=firefox",
            "--ytdl-format=best[height<=720]/best",
            url,
        ]
    )


@app.get("/pause")
def pause():
    return send_mpv_command(["cycle", "pause"])


@app.get("/stop", response_class=HTMLResponse)
def stop(request: Request):
    global current_video

def stop_player():
    global current_player

    subprocess.run(
        ["pkill", "-f", "mpv"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    current_player = None


def render_home(request, query=None, videos=None, current_video=None):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "query": query,
            "videos": videos or [],
            "current_video": current_video if current_video is not None else globals()["current_video"],
        },
    )


def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(
            f"ytsearch10:{query}",
            download=False,
        )

    videos = []

    for video in results.get("entries", []):
        videos.append(
            {
                "title": video.get("title"),
                "id": video.get("id"),
            }
        )

    return videos



def start_video(video_id):
    current_player = subprocess.Popen(
    [
        "mpv",
        "--fullscreen",
        "--force-window=yes",
        f"--input-ipc-server={MPV_SOCKET}",
        "--ytdl-raw-options=cookies-from-browser=firefox",
        "--ytdl-format=best[height<=720]/best",
        url,
    ]
)
    
def stop_player():
    global current_player

    if current_player is not None:
        current_player.kill()
        current_player.wait()
        current_player = None

        

def remove_old_socket():
    socket_path = Path(MPV_SOCKET)

    if socket_path.exists():
        socket_path.unlink()


def send_mpv_command(command):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(MPV_SOCKET)

            message = json.dumps(
                {
                    "command": command
                }
            ) + "\n"

            client.send(message.encode())

        return {
            "ok": True
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }