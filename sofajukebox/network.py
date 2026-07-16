from __future__ import annotations

import socket


def get_lan_ip() -> str:
    """Return the likely LAN IP address of this machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        pass

    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def join_url_from_request(request_host: str) -> str:
    """Build a phone-friendly local URL for joining JulesTube."""
    host, port = _split_host_port(request_host)

    if host in {"127.0.0.1", "localhost", "0.0.0.0", "::1"}:
        host = get_lan_ip()

    return f"http://{host}:{port}/"


def _split_host_port(request_host: str) -> tuple[str, str]:
    request_host = (request_host or "").strip()

    if not request_host:
        return get_lan_ip(), "5050"

    if request_host.startswith("["):
        # Basic IPv6 bracket handling. Not our normal use case, but harmless.
        closing = request_host.find("]")
        host = request_host[1:closing]
        rest = request_host[closing + 1 :]
        port = rest[1:] if rest.startswith(":") else "5050"
        return host, port or "5050"

    if ":" in request_host:
        host, port = request_host.rsplit(":", 1)
        return host, port or "5050"

    return request_host, "5050"
