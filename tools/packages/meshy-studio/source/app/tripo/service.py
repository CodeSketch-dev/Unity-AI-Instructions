from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

from app.automation.model_export import job_folder, package_model
from app.security.credentials import CredentialStore
from app.tripo.client import TripoClient, TripoError
from app.tripo.options import TripoOptions

KEY_ACCOUNT, KEY_KIND = "tripo", "api_key"
TERMINAL = ("Completed", "Failed")


class TripoService:
    """Own queue for Tripo jobs (JSON file, up to 2 in parallel). Independent of the Meshy browser pipeline."""

    def __init__(self, root: Path, export_dir: Callable[[], Path], creds: CredentialStore, *,
                 client_factory: Callable[[str], TripoClient] | None = None, packager: Callable[..., dict] = package_model, workers: int = 2):
        self.root = Path(root)
        self._export_dir = export_dir
        self._creds = creds
        self._factory = client_factory or (lambda key: TripoClient(key))
        self._packager = packager
        self._path = self.root / "data" / "tripo_jobs.json"
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tripo")

    # ---- key -------------------------------------------------------------------------------------------------------------
    def set_key(self, key: str) -> None:
        self._creds.set(KEY_ACCOUNT, KEY_KIND, key.strip())

    def has_key(self) -> bool:
        return bool(self._creds.get(KEY_ACCOUNT, KEY_KIND))

    def _client(self) -> TripoClient:
        return self._factory(self._creds.get(KEY_ACCOUNT, KEY_KIND) or "")

    def balance(self) -> int:
        client = self._client()
        try:
            return client.balance()
        finally:
            client.close()

    # ---- job store -------------------------------------------------------------------------------------------------------
    def _load(self) -> list[dict[str, Any]]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def _save(self, jobs: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(jobs, stream, indent=1)
        os.replace(temp, self._path)

    def _update(self, job_id: int, **fields: Any) -> None:
        with self._lock:
            jobs = self._load()
            for job in jobs:
                if job["id"] == job_id:
                    job.update(fields, updated=time.strftime("%Y-%m-%d %H:%M:%S"))
            self._save(jobs)

    def jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._load()

    def job(self, job_id: int) -> dict[str, Any] | None:
        return next((j for j in self.jobs() if j["id"] == job_id), None)

    # ---- submit / run ----------------------------------------------------------------------------------------------------
    def submit(self, image: str | Path, options: TripoOptions | None = None, note: str = "", *, run: bool = True) -> int:
        image = Path(image)
        if not image.is_file():
            raise TripoError(f"Image not found: {image}")
        if not self.has_key():
            raise TripoError("No Tripo API key saved")
        opts = (options or TripoOptions()).normalized()
        with self._lock:
            jobs = self._load()
            job_id = max((j["id"] for j in jobs), default=0) + 1
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            jobs.append({"id": job_id, "image": str(image), "note": note, "status": "Pending", "progress": 0, "error": None,
                         "task_id": None, "result": None, "options": json.loads(opts.to_json()), "created": stamp, "updated": stamp})
            self._save(jobs)
        if run:
            self._pool.submit(self.run_job, job_id)
        return job_id

    def run_job(self, job_id: int) -> None:
        job = self.job(job_id)
        if job is None:
            return
        client = None
        try:
            client = self._client()
            opts = TripoOptions.from_dict(job["options"])
            self._update(job_id, status="Uploading", progress=2)
            kind, token = client.upload(Path(job["image"]))
            self._update(job_id, status="Generating", progress=5)
            task_id = client.create_task(opts.task_body(kind, token))  # spends credits: never retried automatically
            self._update(job_id, task_id=task_id)
            info = client.wait(task_id, on_progress=lambda p, s: self._update(job_id, progress=max(5, min(95, p)), status="Generating"))
            if not opts.download:
                self._update(job_id, status="Completed", progress=100, model_url=client.model_url(info),
                             error="generated on Tripo; not downloaded (Download result is off)")
                return
            self._update(job_id, status="Downloading", progress=96)
            folder = job_folder(self._export_dir() / "tripo", job["image"])
            glb = client.download(client.model_url(info), folder / f"{Path(job['image']).stem}.glb")
            report = self._packager(glb, self.root)
            self._update(job_id, status="Completed", progress=100, result=str(folder), error="; ".join(report.get("warnings", [])) or None)
        except Exception as error:  # noqa: BLE001  any failure must end the job visibly
            self._update(job_id, status="Failed", error=f"{type(error).__name__}: {error}")
        finally:
            if client is not None:
                client.close()

    def wait_all(self, timeout: float = 600.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and any(j["status"] not in TERMINAL for j in self.jobs()):
            time.sleep(0.5)
