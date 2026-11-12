from __future__ import annotations

import mimetypes
import time
from pathlib import Path
from typing import Any, Callable

import httpx

BASE_URL = "https://api.tripo3d.ai/v2/openapi"
DONE = {"success"}
FAILED = {"failed", "cancelled", "banned", "expired", "unknown"}


class TripoError(RuntimeError):
    pass


class TripoClient:
    """Thin client. `transport` lets tests inject httpx.MockTransport. Task creation is never retried (it spends credits)."""

    def __init__(self, api_key: str, *, transport: httpx.BaseTransport | None = None, base_url: str = BASE_URL, timeout: float = 60.0):
        if not api_key:
            raise TripoError("No Tripo API key. Paste it in the Tripo tab (platform.tripo3d.ai -> API Keys).")
        self._transport = transport
        self._http = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._http.close()

    @staticmethod
    def _data(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            raise TripoError(f"HTTP {response.status_code}: not JSON") from None
        if response.status_code >= 400 or payload.get("code", 0) != 0:
            hint = payload.get("suggestion") or ""
            raise TripoError(f"Tripo error {payload.get('code', response.status_code)}: {payload.get('message', response.reason_phrase)} {hint}".strip())
        return payload.get("data") or {}

    def balance(self) -> int:
        return int(self._data(self._http.get("/user/balance")).get("balance", 0))

    def upload(self, image: Path) -> tuple[str, str]:
        kind = (image.suffix.lower().lstrip(".") or "png").replace("jpeg", "jpg")
        mime = mimetypes.guess_type(image.name)[0] or "image/png"
        with image.open("rb") as stream:
            data = self._data(self._http.post("/upload", files={"file": (image.name, stream, mime)}))
        token = data.get("image_token")
        if not token:
            raise TripoError("Upload returned no image_token")
        return kind, token

    def create_task(self, body: dict) -> str:
        task_id = self._data(self._http.post("/task", json=body)).get("task_id")
        if not task_id:
            raise TripoError("Task creation returned no task_id")
        return task_id

    def task(self, task_id: str) -> dict[str, Any]:
        return self._data(self._http.get(f"/task/{task_id}"))

    def wait(self, task_id: str, *, poll: float = 3.0, timeout: float = 1500.0, on_progress: Callable[[int, str], None] | None = None,
             sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
        deadline = clock() + timeout
        while True:
            info = self.task(task_id)
            status = str(info.get("status", "unknown")).lower()
            if on_progress:
                on_progress(int(info.get("progress") or 0), status)
            if status in DONE:
                return info
            if status in FAILED:
                raise TripoError(f"Tripo task {status}")
            if clock() > deadline:
                raise TripoError("Tripo task timed out (still running on Tripo; check the dashboard)")
            sleep(poll)

    @staticmethod
    def model_url(info: dict[str, Any]) -> str:
        output = info.get("output") or {}
        for key in ("pbr_model", "model", "base_model"):
            value = output.get(key)
            url = value.get("url") if isinstance(value, dict) else value
            if url:
                return url
        raise TripoError("Finished task has no model URL")

    def download(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=300.0, follow_redirects=True, transport=self._transport) as plain:  # signed URL: no auth header
            response = plain.get(url)
        if response.status_code >= 400 or not response.content:
            raise TripoError(f"Model download failed: HTTP {response.status_code}")
        dest.write_bytes(response.content)
        return dest
