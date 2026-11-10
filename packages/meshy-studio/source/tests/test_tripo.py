from __future__ import annotations

import json

import httpx
import pytest

from app.security.credentials import MemoryCredentialStore
from app.tripo.client import TripoClient, TripoError
from app.tripo.options import MAX_FACES, MIN_FACES, TripoOptions
from app.tripo.service import TripoService


def make_transport(state: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        state.setdefault("calls", []).append((request.method, path))
        if path.endswith("/user/balance"):
            return httpx.Response(200, json={"code": 0, "data": {"balance": 200}})
        if path.endswith("/upload"):
            return httpx.Response(200, json={"code": 0, "data": {"image_token": "tok1"}})
        if path.endswith("/task") and request.method == "POST":
            state["body"] = json.loads(request.content)
            return httpx.Response(200, json={"code": 0, "data": {"task_id": "t1"}})
        if "/task/t1" in path:
            state["polls"] = state.get("polls", 0) + 1
            if state["polls"] < 2:
                return httpx.Response(200, json={"code": 0, "data": {"status": "running", "progress": 40}})
            return httpx.Response(200, json={"code": 0, "data": {"status": "success", "progress": 100,
                                                                 "output": {"pbr_model": "https://cdn.example/m.glb"}}})
        if request.url.host == "cdn.example":
            return httpx.Response(200, content=b"glTFfake")
        return httpx.Response(404, json={"code": 404, "message": "nope"})
    return httpx.MockTransport(handler)


def test_options_clamp_and_body():
    o = TripoOptions(face_limit=10, texture_quality="bogus", orientation="x").normalized()
    assert o.face_limit == MIN_FACES and o.texture_quality == "detailed" and o.orientation == "default"
    assert TripoOptions(face_limit=10**9).normalized().face_limit == MAX_FACES
    body = TripoOptions().task_body("png", "tok")
    assert body["type"] == "image_to_model" and body["file"] == {"type": "png", "file_token": "tok"} and body["smart_low_poly"] is True
    assert "smart_low_poly" not in TripoOptions(smart_low_poly=False).task_body("png", "t")


def test_client_requires_key():
    with pytest.raises(TripoError):
        TripoClient("")


def test_error_envelope_becomes_tripo_error():
    client = TripoClient("k", transport=make_transport({}))
    with pytest.raises(TripoError):
        client.task("missing")


def test_full_job_flow(tmp_path, monkeypatch):
    state: dict = {}
    creds = MemoryCredentialStore()
    image = tmp_path / "bench.png"
    image.write_bytes(b"\x89PNG fake")
    svc = TripoService(tmp_path, lambda: tmp_path / "export", creds,
                       client_factory=lambda key: TripoClient(key, transport=make_transport(state)),
                       packager=lambda glb, root: {"warnings": []})
    with pytest.raises(TripoError):
        svc.submit(image)                      # no key yet
    svc.set_key("tsk_x")
    monkeypatch.setattr("time.sleep", lambda s: None)
    job_id = svc.submit(image, TripoOptions(download=True), run=False)
    svc.run_job(job_id)
    job = svc.job(job_id)
    assert job["status"] == "Completed", job
    assert job["progress"] == 100 and job["task_id"] == "t1"
    assert state["body"]["face_limit"] == 10000
    assert sum(1 for m, p in state["calls"] if m == "POST" and p.endswith("/task")) == 1  # credit-spending call happens once
    assert any(f.suffix == ".glb" for f in (tmp_path / "export" / "tripo").rglob("*"))


def test_failed_task_is_recorded(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/upload"):
            return httpx.Response(200, json={"code": 2010, "message": "insufficient credit"})
        return httpx.Response(404)
    creds = MemoryCredentialStore()
    image = tmp_path / "a.png"
    image.write_bytes(b"x")
    svc = TripoService(tmp_path, lambda: tmp_path, creds,
                       client_factory=lambda key: TripoClient(key, transport=httpx.MockTransport(handler)))
    svc.set_key("k")
    job_id = svc.submit(image, run=False)
    svc.run_job(job_id)
    job = svc.job(job_id)
    assert job["status"] == "Failed" and "insufficient credit" in job["error"]


def test_generate_only_skips_download(tmp_path, monkeypatch):
    state: dict = {}
    creds = MemoryCredentialStore()
    image = tmp_path / "b.png"
    image.write_bytes(b"x")
    svc = TripoService(tmp_path, lambda: tmp_path / "export", creds,
                       client_factory=lambda key: TripoClient(key, transport=make_transport(state)))
    svc.set_key("k")
    monkeypatch.setattr("time.sleep", lambda s: None)
    job_id = svc.submit(image, run=False)
    svc.run_job(job_id)
    job = svc.job(job_id)
    assert job["status"] == "Completed" and job["model_url"].endswith("m.glb") and not (tmp_path / "export").exists()
