"""HTTP client for the semantic action server embedded in UrbanGround."""

from __future__ import annotations

import base64
import time
from typing import Any

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:8081"


def decode_data_url(data_url: str) -> bytes:
    """Strip a data-URL prefix and decode its base64 payload."""
    _, _, payload = data_url.partition(",")
    return base64.b64decode(payload)


class AgentClient:
    """Drive UrbanGround through its structured observation and action endpoints."""

    def __init__(self, base_url: str | object = DEFAULT_BASE_URL):
        # Older repository probes passed their process/session handle here. Direct local HTTP
        # no longer needs that handle, but accepting it keeps those diagnostics importable.
        if not isinstance(base_url, str):
            base_url = DEFAULT_BASE_URL
        self.base_url = base_url.rstrip("/")
        self._http = requests.Session()

    def _request(self, method: str, path: str, *, timeout: float = 30, **kwargs) -> requests.Response:
        response = self._http.request(
            method, f"{self.base_url}{path}", timeout=timeout, **kwargs
        )
        response.raise_for_status()
        return response

    def wait_until_ready(self, timeout: float, poll_interval: float = 1.0) -> None:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self.get_state()
                return
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(poll_interval)
        raise TimeoutError(
            f"UrbanGround action server did not become ready at {self.base_url} "
            f"within {timeout:.1f}s: {last_error}"
        )

    def get_state(self) -> dict[str, Any]:
        return self._request("GET", "/state").json()

    def task_enter(self, task_id: str) -> dict[str, Any]:
        """Load a task from the task directory bundled beside the running application."""
        return self._request(
            "POST", "/task/enter", json={"id": task_id}, timeout=60
        ).json()

    def task_get(self) -> dict[str, Any]:
        return self._request("GET", "/task").json()

    def task_exit(self) -> dict[str, Any]:
        response = self._request("POST", "/task/exit")
        return response.json() if response.content else {}

    def act(
        self,
        action: dict[str, Any],
        timeout: int = 30,
        interval: float = 0.0,
        max_frames: int = 60,
    ) -> dict[str, Any]:
        action = dict(action)
        if action.get("action") in {"move", "sprint"}:
            try:
                action["seconds"] = min(2.0, max(0.05, float(action.get("seconds", 0.5))))
            except (TypeError, ValueError):
                action["seconds"] = 0.5
            if "jump_at" in action:
                try:
                    action["jump_at"] = min(
                        action["seconds"], max(0.0, float(action["jump_at"]))
                    )
                except (TypeError, ValueError):
                    action["jump_at"] = 0.0
        params = {"interval": interval, "max_frames": max_frames} if interval > 0 else None
        return self._request(
            "POST", "/action", json=action, params=params, timeout=timeout
        ).json()

    def act_with_frames(
        self, action: dict[str, Any], timeout: int = 30,
        interval: float = 0.3, max_frames: int = 60,
    ) -> list[bytes]:
        reply = self.act(action, timeout=timeout, interval=interval, max_frames=max_frames)
        return [decode_data_url(value) for value in reply.get("images", [])]

    def screenshot(self) -> bytes:
        return self._request("GET", "/screenshot", timeout=20).content

    def move(self, direction: str, seconds: float = 0.5, sprint: bool = False, **kwargs) -> dict:
        return self.act({"action": "sprint" if sprint else "move", "dir": direction,
                         "seconds": seconds, **kwargs})

    def jump(self) -> dict:
        return self.act({"action": "jump"})

    def look(self, yaw: float = 0.0, pitch: float = 0.0) -> dict:
        return self.act({"action": "look", "yaw": yaw, "pitch": pitch})

    def open_map(self) -> dict:
        return self.act({"action": "open_map"})

    def close_map(self) -> dict:
        return self.act({"action": "close_map"})

    def map_select(self, x: float, y: float) -> dict:
        return self.act({"action": "map_select", "x": x, "y": y})

    def map_orbit(self, yaw: float = 0.0, pitch: float = 0.0) -> dict:
        return self.act({"action": "map_orbit", "yaw": yaw, "pitch": pitch})

    def map_zoom(self, factor: float) -> dict:
        return self.act({"action": "map_zoom", "factor": factor})

    def map_pan(self, east: float = 0.0, north: float = 0.0) -> dict:
        return self.act({"action": "map_pan", "east": east, "north": north})

    def map_teleport(self) -> dict:
        return self.act({"action": "map_teleport"}, timeout=15)

    def teleport(self, lat: float, lon: float, height: float) -> dict:
        return self.act(
            {"action": "teleport", "lat": lat, "lon": lon, "height": height}, timeout=15
        )

    def navigate(self) -> dict:
        return self.act({"action": "navigate"}, timeout=25)

    def clear_route(self) -> dict:
        return self.act({"action": "clear_route"})

    def show_network(self) -> dict:
        return self.act({"action": "show_network"}, timeout=20)

    def hide_network(self) -> dict:
        return self.act({"action": "hide_network"})

    def toggle_network(self) -> dict:
        return self.act({"action": "toggle_network"}, timeout=20)

    def identify_location(self) -> dict:
        return self.act({"action": "identify_location"}, timeout=25)

    def where_am_i(self) -> dict:
        return self.act({"action": "where_am_i"}, timeout=20)

    def set_weather(self, weather: str) -> dict:
        return self.act({"action": "set_weather", "weather": weather})

    def set_time(self, hour: int, minute: int = 0) -> dict:
        return self.act({"action": "set_time", "hour": hour, "minute": minute})

    def enable_pedestrians(self) -> dict:
        return self.act({"action": "enable_pedestrians"}, timeout=15)

    def disable_pedestrians(self) -> dict:
        return self.act({"action": "disable_pedestrians"})
