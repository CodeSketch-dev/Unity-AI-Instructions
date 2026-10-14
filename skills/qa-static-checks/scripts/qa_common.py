"""Shared helpers for the static QA scanners (stdlib only, no Unity needed).

Every scanner returns a list of findings: {rule, severity, file, line, msg}. severity is "error" (hard, fails the gate)
or "warn" (soft). Exit code of a scanner CLI is 1 when any error exists, else 0.
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {"Library", "Temp", "obj", "Logs", "Build", "Builds", ".git", "node_modules", "UserSettings"}


def finding(rule, severity, file, line, msg):
    return {"rule": rule, "severity": severity, "file": file.replace("\\", "/"), "line": line, "msg": msg}


def read_text(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def walk(root, exts, subdirs=("Assets", "Packages")):
    """Yield absolute paths of files with one of exts under root/<subdirs>, skipping generated folders."""
    for sub in subdirs:
        base = os.path.join(root, sub)
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for n in fn:
                if n.lower().endswith(exts):
                    yield os.path.join(dp, n)


def rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def select_files(root, exts, files=None, subdirs=("Assets", "Packages")):
    """files = explicit list (relative or absolute) for diff-scoped runs; otherwise walk the project."""
    if files:
        out = []
        for f in files:
            p = f if os.path.isabs(f) else os.path.join(root, f)
            if p.lower().endswith(exts) and os.path.isfile(p):
                out.append(p)
        return out
    return list(walk(root, exts, subdirs))


def first_party(root, name="Assets/_Game"):
    """Scope runtime-code rules to the project's own code; vendor SDKs under Assets/ are not ours to lint. Falls back to Assets."""
    return name if os.path.isdir(os.path.join(root, name)) else "Assets"


def base_parser(desc):
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--project", default=".", help="Unity project root")
    ap.add_argument("--files", nargs="*", help="limit to these files (diff-scoped run)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON lines")
    ap.add_argument("--first-party", default="Assets/_Game", help="first-party code folder (falls back to Assets)")
    return ap


def report(findings, as_json=False, out=None):
    out = out or sys.stdout
    errors = sum(1 for f in findings if f["severity"] == "error")
    warns = len(findings) - errors
    for f in findings:
        if as_json:
            out.write(json.dumps(f) + "\n")
        else:
            out.write("%s %s %s:%s %s\n" % (f["severity"].upper(), f["rule"], f["file"], f["line"], f["msg"]))
    out.write("%d error(s), %d warning(s)\n" % (errors, warns))
    return 1 if errors else 0


ALLOW_RE = re.compile(r"//\s*qa-allow:\s*([A-Z0-9-]+)(?:\s+(\S.*))?")


def allowed(line_text, rule):
    """'// qa-allow: RULE reason' on the line suppresses RULE; the reason is mandatory."""
    m = ALLOW_RE.search(line_text)
    if not m or m.group(1) != rule:
        return None
    return bool(m.group(2))
