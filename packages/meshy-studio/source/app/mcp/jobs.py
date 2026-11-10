"""Tools that drive the running Meshy AI Studio app through its job queue (the app owns the browser and the CAPTCHA)."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from app.automation.meshy_export import inspect_glb
from app.core.job_options import DEFAULT_POLYCOUNT, MAX_POLYCOUNT, MIN_POLYCOUNT, GenMode, JobOptions, RigType
from app.core.pipeline import runner_lock_held, validate_image
from app.mcp import context
from app.mcp.registry import INT, STR, schema, tool

_UNUSABLE = {"quota limited", "needs verification", "login failed", "busy", "invalid credentials"}
OPTIONS_PROPS = {
    "mode": {"type": "string", "enum": ["topology", "automatic"],
             "description": "topology (default): Meshy 7 + Smart Topology with YOUR polygon count, textured in one pass, no remesh. "
                            "automatic: Meshy's own very dense mesh, texture, then remesh to 10K."},
    "polycount": {"type": "integer", "minimum": MIN_POLYCOUNT, "maximum": MAX_POLYCOUNT,
                  "description": f"Target triangles for topology mode ({MIN_POLYCOUNT}-{MAX_POLYCOUNT}, default {DEFAULT_POLYCOUNT}). "
                                 "Choose per object: detailed hero pieces high, small or distant props low (see triangle_budget_guide)."},
    "rig": {"type": "boolean", "description": "Auto-rig a skeleton after everything else (extra credits)."},
    "rig_type": {"type": "string", "enum": ["humanoid", "quadruped", "auto"]},
    "note": STR,
}


def _options(args: dict) -> JobOptions:
    return JobOptions(GenMode(args.get("mode", "topology")), int(args.get("polycount", DEFAULT_POLYCOUNT)),
                      bool(args.get("rig", False)), RigType(args.get("rig_type", "auto"))).normalized()


def app_running() -> bool:
    return runner_lock_held(context.lock_path())


def _needs_user(job) -> str | None:
    if job.status == "Paused" and job.error and "CAPTCHA" in job.error.upper():
        return "captcha"
    return None


def _describe(db, job, with_files: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {"job_id": job.id, "image": Path(job.image_path).name, "status": job.status, "progress": job.progress,
                           "error": job.error, "account_id": job.account_id, "submitted_to_meshy": bool(job.submitted),
                           "queue_position": db.queue_position(job.id),
                           "options": json.loads(JobOptions.from_json(job.options).to_json())}
    if _needs_user(job):
        out["needs_user"] = "captcha"
        out["hint"] = "Ask the owner to solve the CAPTCHA in the Meshy browser window, then call resume_jobs."
    if job.result_path and Path(job.result_path).is_file():
        folder = Path(job.result_path).parent
        out["result_path"], out["result_folder"] = job.result_path, str(folder)
        try:
            out["triangles"] = inspect_glb(job.result_path)["triangles"]
        except Exception:
            pass
        if with_files:
            out["files"] = sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())
    return out


@tool("app_status", "State of the Meshy AI Studio app: is the exe running, queue counts, usable accounts and credits, and what is "
                    "blocking work (no account, captcha waiting for the owner). Call this first.", schema())
def app_status(args: dict) -> dict:
    database = context.db()
    try:
        jobs, accounts = database.list_jobs(), database.list_accounts()
        counts: dict[str, int] = {}
        for job in jobs:
            counts[job.status] = counts.get(job.status, 0) + 1
        usable = [a for a in accounts if a.authorized and a.status.lower() not in _UNUSABLE]
        waiting = [j.id for j in jobs if _needs_user(j)]
        running = app_running()
        blockers = []
        if not running:
            blockers.append("The app is not running: call launch_app, or ask the owner to open MeshyAIStudio.exe (queued jobs wait for it).")
        if not accounts:
            blockers.append("No Meshy accounts yet: the app adopts/creates Purelymail mailboxes automatically once jobs are waiting.")
        elif not usable:
            blockers.append("No account can run a job right now (no credit / resting / needs verification); auto-create may add one.")
        if waiting:
            blockers.append(f"Jobs {waiting} wait for the owner to solve a CAPTCHA in the Meshy browser window, then call resume_jobs.")
        return {"app_running": running, "queue": counts, "accounts_total": len(accounts), "accounts_usable": len(usable),
                "credits": {a.email: a.credit_balance for a in accounts}, "jobs_waiting_for_owner": waiting,
                "export_folder": str(context.export_dir()), "blockers": blockers}
    finally:
        database.close()


@tool("launch_app", "Start MeshyAIStudio.exe (visible window, so the owner can solve CAPTCHAs). No-op if it is already running.", schema())
def launch_app(args: dict) -> dict:
    if app_running():
        return {"started": False, "reason": "already running"}
    exe = Path(os.environ.get("MESHY_APP_EXE") or context.PACKAGE / "MeshyAIStudio.exe")
    if not exe.is_file():
        return {"started": False, "reason": f"{exe} not found: run publish.bat in the meshy-studio folder first"}
    subprocess.Popen([str(exe)], cwd=str(exe.parent), creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    return {"started": True, "exe": str(exe), "note": "The first start unpacks for 5-30 s; poll app_status."}


@tool("generate_model", "Queue ONE image for a 3D model. You choose the mesh detail per object via mode/polycount. Returns job_id; "
                        "then wait_for_jobs. The app must be running (see app_status / launch_app).",
      schema(["image_path"], image_path=STR, **OPTIONS_PROPS))
def generate_model(args: dict) -> dict:
    path = validate_image(args["image_path"])
    options = _options(args)
    database = context.db()
    try:
        job_id = database.create_job(str(path.resolve()), str(args.get("note", "")), options=options.to_json())
    finally:
        database.close()
    out = {"job_id": job_id, "status": "Pending", "options": json.loads(options.to_json()), "app_running": app_running()}
    if not out["app_running"]:
        out["warning"] = "App is not running: the job waits. Call launch_app or ask the owner to open MeshyAIStudio.exe."
    return out


@tool("generate_models", "Queue several images at once, each with its OWN options (e.g. 12000 triangles for the hero gate, 800 for small "
                         "rocks). Items: {image_path, mode?, polycount?, rig?, rig_type?, note?}.",
      schema(["items"], items={"type": "array", "items": {"type": "object", "required": ["image_path"],
                                                           "properties": {"image_path": STR, **OPTIONS_PROPS}}}))
def generate_models(args: dict) -> dict:
    queued, rejected = [], []
    for index, item in enumerate(args.get("items", [])):
        try:
            queued.append(generate_model(item))
        except (ValueError, KeyError) as error:
            rejected.append({"index": index, "image_path": item.get("image_path"), "error": str(error)})
    return {"queued": queued, "rejected": rejected, "app_running": app_running()}


@tool("job_status", "Full status of one job: progress, error, options, result folder, files and triangle count.",
      schema(["job_id"], job_id=INT))
def job_status(args: dict) -> dict:
    database = context.db()
    try:
        try:
            return _describe(database, database.get_job(int(args["job_id"])))
        except KeyError:
            return {"error": "job not found"}
    finally:
        database.close()


@tool("wait_for_jobs", "Block until all listed jobs finish (Completed/Failed/Canceled), or one needs the owner (CAPTCHA), or the timeout "
                       "(default 50 s; call again to keep waiting). Returns each job's status.",
      schema(["job_ids"], job_ids={"type": "array", "items": INT}, timeout_s=INT))
def wait_for_jobs(args: dict) -> dict:
    ids = [int(i) for i in args["job_ids"]]
    deadline = time.monotonic() + max(1, min(int(args.get("timeout_s", 50)), 300))
    while True:
        database = context.db()
        try:
            jobs = [database.get_job(i) for i in ids]
            states = [_describe(database, j, with_files=False) for j in jobs]
        finally:
            database.close()
        done = all(j.status in context.TERMINAL for j in jobs)
        owner = [s["job_id"] for s in states if s.get("needs_user")]
        if done or owner or time.monotonic() >= deadline:
            return {"all_done": done, "needs_owner": owner, "timed_out": not done and not owner, "jobs": states,
                    "app_running": app_running()}
        time.sleep(2)


@tool("list_jobs", "Recent jobs (newest first), optionally filtered by status.", schema(limit=INT, status=STR))
def list_jobs(args: dict) -> list:
    database = context.db()
    try:
        jobs = database.list_jobs()
        if args.get("status"):
            jobs = [j for j in jobs if j.status.lower() == str(args["status"]).lower()]
        return [_describe(database, j, with_files=False) for j in jobs[: int(args.get("limit", 20))]]
    finally:
        database.close()


@tool("cancel_jobs", "Cancel queued jobs (the rest move up); a running job stops at its next step. A task already submitted to Meshy "
                     "keeps running on their server.", schema(["job_ids"], job_ids={"type": "array", "items": INT}))
def cancel_jobs(args: dict) -> dict:
    database = context.db()
    try:
        return database.cancel_jobs([int(i) for i in args["job_ids"]])
    finally:
        database.close()


@tool("pause_jobs", "Pause queued jobs.", schema(["job_ids"], job_ids={"type": "array", "items": INT}))
def pause_jobs(args: dict) -> dict:
    database = context.db()
    try:
        return {"paused": database.pause_jobs([int(i) for i in args["job_ids"]])}
    finally:
        database.close()


@tool("resume_jobs", "Resume paused jobs (use after the owner solved a CAPTCHA).", schema(["job_ids"], job_ids={"type": "array", "items": INT}))
def resume_jobs(args: dict) -> dict:
    database = context.db()
    try:
        ids = [int(i) for i in args["job_ids"]]
        resumed = database.resume_jobs(ids)
        for job_id in ids:  # same effect as the app's Resume: re-enable the account that waited for the CAPTCHA
            job = database.get_job(job_id)
            if job.account_id and job.error and "CAPTCHA" in job.error.upper():
                database.mark_account(job.account_id, "Ready", authorized=True)
        return {"resumed": resumed}
    finally:
        database.close()


@tool("retry_jobs", "Re-queue Failed/Canceled jobs that were NOT submitted to Meshy yet. A submitted job is refused: a retry could "
                    "spend credits twice; check the Meshy workspace and ask the owner.",
      schema(["job_ids"], job_ids={"type": "array", "items": INT}))
def retry_jobs(args: dict) -> dict:
    database = context.db()
    try:
        ids = [int(i) for i in args["job_ids"]]
        blocked = [i for i in ids if database.get_job(i).submitted]
        ok = [i for i in ids if i not in blocked]
        return {"requeued": database.requeue_jobs(ok) if ok else 0, "refused_already_submitted": blocked}
    finally:
        database.close()


@tool("list_accounts", "Meshy accounts with status, credits and cooldown (never passwords).", schema())
def list_accounts(args: dict) -> list:
    database = context.db()
    try:
        return [{"id": a.id, "email": a.email, "status": a.status, "authorized": a.authorized, "credits": a.credit_balance,
                 "cooldown_until": a.cooldown_until} for a in database.list_accounts()]
    finally:
        database.close()
