"""Single-instance Graphify watcher for the Unity project (code-only, no LLM).

Watches only first-party C# folders (not Library/Temp), debounces bursts, then runs
`graphify update <project>` (AST only; graphify holds its own rebuild lock, so any
concurrent `graphify update` from an agent or git hook is safe).

Run it through docs/tools/graphify_ctl.sh, not directly.
Usage: python graphify_watch.py <project_root> [--debounce 5] [--dirs Assets/_Game ...]
"""
import argparse, msvcrt, os, subprocess, sys, time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

EXTS = {".cs"}
SKIP_PARTS = {"graphify-out", "Library", "Temp", "obj", "Obj", "Logs", "Build", "Builds", "UserSettings"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--debounce", type=float, default=5.0)
    ap.add_argument("--dirs", nargs="*", default=["Assets/_Game", "Assets/GAME_STEAL_MATTER_EGG"])
    a = ap.parse_args()
    root = Path(a.root).resolve()
    out = root / "graphify-out"
    out.mkdir(exist_ok=True)

    # single instance: hold a byte-range lock for the process lifetime
    lock = open(out / "watcher.lock", "a+")
    try:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("another watcher already holds the lock; exiting", flush=True)
        return 2
    (out / "watcher.pid").write_text(str(os.getpid()))

    state = {"last": 0.0, "pending": set(), "shrink": False}

    def wanted(p):
        p = Path(os.fsdecode(p))
        return p.suffix.lower() in EXTS and not (SKIP_PARTS & set(p.parts))

    class H(FileSystemEventHandler):
        def on_any_event(self, ev):
            if ev.is_directory or ev.event_type in ("opened", "closed_no_write", "closed"):
                return
            if ev.event_type in ("deleted", "moved"):
                state["shrink"] = True  # plain update keeps deleted files; --force lets the graph shrink
            for p in (ev.src_path, getattr(ev, "dest_path", "")):
                if p and wanted(p):
                    state["pending"].add(os.fsdecode(p))
                    state["last"] = time.monotonic()

    obs = Observer()
    watched = []
    for d in a.dirs:
        p = root / d
        if p.is_dir():
            obs.schedule(H(), str(p), recursive=True)
            watched.append(str(p))
    obs.start()
    print(f"[watch] pid={os.getpid()} dirs={watched} debounce={a.debounce}s", flush=True)
    try:
        while True:
            time.sleep(1.0)
            if state["pending"] and time.monotonic() - state["last"] >= a.debounce:
                n = len(state["pending"])
                state["pending"].clear()
                cmd = ["graphify", "update", str(root)] + (["--force"] if state["shrink"] else [])
                state["shrink"] = False
                t = time.time()
                r = subprocess.run(cmd, cwd=root, capture_output=True,
                                   text=True, creationflags=0x00004000 | 0x08000000)  # BELOW_NORMAL | NO_WINDOW
                tail = (r.stdout or "").strip().splitlines()[-2:]
                print(f"[watch] {n} cs change(s) -> update rc={r.returncode} {time.time()-t:.1f}s | {' / '.join(tail)}", flush=True)
                if r.returncode:
                    print((r.stderr or "")[-500:], flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        obs.stop()
        obs.join()
        try:
            (out / "watcher.pid").unlink()
        except OSError:
            pass


sys.exit(main() or 0)
