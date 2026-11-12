"""Usage: python run_lint.py <file>...      lint the given files
       python run_lint.py --changed        lint every changed/untracked file in `git status` of the cwd
Exit 2 + violations on stderr (hook contract). Exit 0 when clean or when the engine itself fails (never block edits on a tool bug)."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def changed_files():
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    r = subprocess.run(["git", "status", "--porcelain", "-z", "-uall"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    entries = r.stdout.split("\0")
    out = []
    i = 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        if e[0] in "RC":  # rename/copy: the next entry is the original path
            i += 1
        p = e[3:]
        if p.endswith(".cs"):
            # realpath on both sides: Windows may hand out 8.3 short paths for one and long paths for the other
            out.append(os.path.relpath(os.path.realpath(os.path.join(top, p)), os.path.realpath(os.getcwd())))
    return out


def hook_files():
    """PostToolUse mode: the tool JSON arrives on stdin; lint only the file that was just edited."""
    import json
    try:
        p = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace")).get("tool_input", {}).get("file_path")
    except ValueError:
        return []
    return [p] if p and p.endswith(".cs") else []


def log_hits(violations):
    """Append one JSON line per violation (rule frequency feeds the harness miner). Size-capped; never raises."""
    if not violations:
        return
    try:
        import json
        import time
        path = os.environ.get("STUDIO_LINT_HITS") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "hits.jsonl")
        cap = int(os.environ.get("STUDIO_LINT_HITS_MAX", "524288"))
        if os.path.isfile(path) and os.path.getsize(path) >= cap:
            return
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            for v in violations:
                fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "file": v.path, "rule": v.rule_id}) + "\n")
    except Exception:
        pass


def main(argv):
    try:
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(errors="replace")
        import engine
        if argv[:1] == ["--hook"]:
            files = hook_files()
        else:
            files = changed_files() if argv[:1] == ["--changed"] else argv
        bad = []
        for f in files:
            if not os.path.isfile(f):
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                bad.extend(engine.lint_text(f, fh.read()))
        for v in bad:
            sys.stderr.write("%s:%d: %s\n" % (v.path, v.line, v.message))
        log_hits(bad)
        return 2 if bad else 0
    except Exception as e:  # engine bug must not block the agent
        sys.stderr.write("lint engine error (ignored): %r\n" % (e,))
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
