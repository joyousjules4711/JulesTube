from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from fauxmo.plugins import FauxmoPlugin


class JulesTubeCommandPlugin(FauxmoPlugin):
    """
    Stateless Alexa command device for JulesTube.

    Alexa sees each command as a smart-home switch.
    'on' triggers the command.
    'off' does nothing.
    get_state always returns 'off', so commands can be repeated.
    """

    def __init__(
        self,
        name: str,
        port: int,
        action: str,
        base_url: str = "http://127.0.0.1:5050",
        **kwargs,
    ):
        self.action = action
        self.base_url = base_url.rstrip("/")
        super().__init__(name=name, port=port, **kwargs)

    def _post(self, path: str, payload: dict | None = None) -> bool:
        data = None
        headers = {}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=1.5) as response:
                return 200 <= response.status < 300
        except URLError:
            return False
        except Exception:
            return False

    def _run_action(self) -> bool:
        if self.action == "play_pause":
            return self._post("/api/control/pause")

        if self.action == "next":
            return self._post("/api/control/next")

        if self.action == "volume_loud":
            return self._post("/api/control/volume", {"volume": 85})

        if self.action == "volume_normal":
            return self._post("/api/control/volume", {"volume": 60})

        if self.action == "volume_quiet":
            return self._post("/api/control/volume", {"volume": 35})

        return False

    def on(self) -> bool:
        return self._run_action()

    def off(self) -> bool:
        # Absichtlich No-Op. So können Alexa-Routinen Geräte wieder ausschalten,
        # ohne den Befehl doppelt auszulösen.
        return True

    def get_state(self) -> str:
        # Immer off, damit Alexa denselben Befehl mehrfach auslösen kann.
        return "off"
