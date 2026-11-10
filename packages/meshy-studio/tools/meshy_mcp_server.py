"""Stdio MCP server so Claude Code / Codex can generate Meshy models.

Tools only enqueue and read state; a single headless runner (`python -m app.runner`)
owns the browser. The server starts that runner when none holds the lock.
Secrets are never returned: account import takes a file path, never inline passwords.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.account_manager import AccountManager  # noqa: E402
from app.core.database import Database  # noqa: E402
from app.core.pipeline import IMAGE_SUFFIXES, MAX_IMAGE_BYTES, runner_lock_held  # noqa: E402
from app.security.credentials import KeyringCredentialStore, MemoryCredentialStore  # noqa: E402

DATA = Path(os.environ.get("MESHY_DATA_DIR") or ROOT)
EXPORT = DATA / "Export"
_MEMORY_STORE = MemoryCredentialStore()


def _db() -> Database:
    return Database(DATA / "data" / "meshy.sqlite3")


def _schema(required=(), **props):
    return {"type": "object", "required": list(required), "properties": props}


TOOLS = [
    {"name": "generate_model", "description": "Queue an image (png/jpg/webp, <=20MB). The app logs in, rotates accounts on quota and generates the 3D model automatically. Returns job_id; poll job_status.",
     "inputSchema": _schema(["image_path"], image_path={"type": "string"}, note={"type": "string"})},
    {"name": "job_status", "description": "Status, progress, error and account of one job.",
     "inputSchema": _schema(["job_id"], job_id={"type": "integer"})},
    {"name": "list_jobs", "description": "Most recent jobs.", "inputSchema": _schema(limit={"type": "integer"})},
    {"name": "list_accounts", "description": "Accounts with health status and quota cooldown (no secrets).", "inputSchema": _schema()},
    {"name": "import_accounts", "description": "Import a .txt file of lines email|password or email|password|recovery_email|totp_secret.",
     "inputSchema": _schema(["file_path"], file_path={"type": "string"})},
    {"name": "list_exports", "description": "Downloaded GLB/FBX/OBJ/STL files in the Export folder.", "inputSchema": _schema()},
]


def ensure_runner() -> bool:
    """Start the headless runner if nobody holds the lock. Returns True if spawned."""
    if os.environ.get("MESHY_NO_SPAWN") == "1" or runner_lock_held(DATA / "data" / "runner.lock"):
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    subprocess.Popen([sys.executable, "-m", "app.runner"], cwd=str(ROOT), creationflags=flags,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def call_tool(name: str, args: dict):
    if name == "generate_model":
        path = Path(str(args.get("image_path", "")))
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("Image must be PNG, JPG, JPEG or WebP")
        if not path.is_file():
            raise ValueError("Image file does not exist")
        if path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image exceeds the 20 MB limit")
        db = _db()
        job_id = db.create_job(str(path.resolve()), str(args.get("note", "")))
        db.close()
        return {"job_id": job_id, "status": "Pending", "runner_started": ensure_runner()}
    if name == "job_status":
        db = _db()
        try:
            job = db.get_job(int(args["job_id"]))
        except KeyError:
            return {"error": "job not found"}
        finally:
            db.close()
        files = []
        if job.result_path and Path(job.result_path).parent.is_dir():
            folder = Path(job.result_path).parent
            files = sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())
        return {"job_id": job.id, "status": job.status, "progress": job.progress, "error": job.error,
                "account_id": job.account_id, "retries": job.retries, "result_path": job.result_path,
                "result_folder": str(Path(job.result_path).parent) if job.result_path else None, "files": files}
    if name == "list_jobs":
        db = _db()
        jobs = db.list_jobs()[: int(args.get("limit", 20))]
        db.close()
        return [{"job_id": j.id, "image": Path(j.image_path).name, "status": j.status, "error": j.error} for j in jobs]
    if name == "list_accounts":
        db = _db()
        accounts = db.list_accounts()
        db.close()
        return [{"id": a.id, "email": a.email, "status": a.status, "authorized": a.authorized,
                 "cooldown_until": a.cooldown_until} for a in accounts]
    if name == "import_accounts":
        store = _MEMORY_STORE if os.environ.get("MESHY_CREDENTIALS") == "memory" else KeyringCredentialStore()
        db = _db()
        result = AccountManager(db, store, DATA / "profiles").import_file(args["file_path"])
        db.close()
        return {"imported": result.imported, "duplicates": result.duplicates, "invalid": result.invalid}
    if name == "list_exports":
        return [{"name": p.name, "path": str(p.resolve()), "bytes": p.stat().st_size}
                for p in EXPORT.glob("*") if p.suffix.lower() in {".glb", ".fbx", ".obj", ".stl"}]
    raise ValueError("Unknown tool")


def reply(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    message["error" if error else "result"] = error or result
    print(json.dumps(message, ensure_ascii=False), flush=True)


def main() -> None:
    for line in sys.stdin:
        request_id = None
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                reply(request_id, {"protocolVersion": request.get("params", {}).get("protocolVersion", "2024-11-05"),
                                   "capabilities": {"tools": {}}, "serverInfo": {"name": "meshy-ai-studio", "version": "2.0"}})
            elif method == "tools/list":
                reply(request_id, {"tools": TOOLS})
            elif method == "tools/call":
                params = request.get("params", {})
                try:
                    data = call_tool(params.get("name"), params.get("arguments") or {})
                    reply(request_id, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]})
                except Exception as error:
                    reply(request_id, {"isError": True, "content": [{"type": "text", "text": str(error)}]})
            elif request_id is not None:
                reply(request_id, {})
        except Exception as error:
            if request_id is not None:
                reply(request_id, error={"code": -32603, "message": str(error)})


if __name__ == "__main__":
    main()
