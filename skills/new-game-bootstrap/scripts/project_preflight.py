"""Repository-level release preflight that needs no Unity (stdlib only).

  py -I project_preflight.py --project P [--gates qa/gates.json]

Checks (error unless noted):
  PKG-UNPINNED     a git dependency in Packages/manifest.json has no tag/sha, or points at main/master/HEAD
  LOCK-MISSING     Packages/packages-lock.json missing or ignored by git
  VERSION-IGNORED  ProjectSettings/ProjectVersion.txt is ignored by git
  IGNORE-MISSING   .gitignore lacks Library/, Temp/, *.keystore, *.jks, *.aab or *.apk
  SECRET-TRACKED   a keystore, jks or google-services.json is tracked by git
  CONFIG           project.config.json missing/invalid (bundle id, semver)
  GATES            qa/gates.json missing or not valid JSON (warn)
Exit 1 when any error exists.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

REQUIRED_IGNORES = ("Library/", "Temp/", "*.keystore", "*.jks", "*.aab", "*.apk")
SECRET_RE = re.compile(r"(\.keystore|\.jks)$|(^|/)google-services\.json$|(^|/)GoogleService-Info\.plist$", re.I)
BUNDLE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){2,}$")


def f(rule, sev, file, msg):
    return {"rule": rule, "severity": sev, "file": file, "msg": msg}


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def ignored(project, path):
    try:
        r = subprocess.run(["git", "-C", project, "check-ignore", "-q", path], capture_output=True, timeout=20)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def tracked_files(project):
    try:
        r = subprocess.run(["git", "-C", project, "ls-files"], capture_output=True, text=True, timeout=60)
        return r.stdout.splitlines() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def check_manifest(project):
    out = []
    text = read(os.path.join(project, "Packages", "manifest.json"))
    if text is None:
        return [f("PKG-UNPINNED", "error", "Packages/manifest.json", "manifest not found")]
    deps = json.loads(text).get("dependencies", {})
    for name, ref in deps.items():
        if isinstance(ref, str) and (ref.startswith("http") or ref.startswith("git") or ".git" in ref):
            m = re.search(r"#(.+)$", ref)
            if not m or m.group(1).lower() in ("main", "master", "head", "develop"):
                out.append(f("PKG-UNPINNED", "error", "Packages/manifest.json", "%s is not pinned to a tag or commit (%s)" % (name, ref)))
    return out


def check_ignore_file(project):
    text = read(os.path.join(project, ".gitignore"))
    if text is None:
        return [f("IGNORE-MISSING", "error", ".gitignore", ".gitignore not found")]
    lines = {l.strip() for l in text.splitlines()}
    out = []
    for need in REQUIRED_IGNORES:
        if not any(l and not l.startswith("#") and fnmatch.fnmatch(need, l.lstrip("/")) for l in lines):
            out.append(f("IGNORE-MISSING", "error", ".gitignore", "missing ignore rule for " + need))
    return out


def check_config(project):
    p = os.path.join(project, "project.config.json")
    text = read(p)
    if text is None:
        return [f("CONFIG", "error", "project.config.json", "not found")]
    try:
        cfg = json.loads(text)
    except ValueError:
        return [f("CONFIG", "error", "project.config.json", "invalid JSON")]
    out = []
    if not BUNDLE_RE.match(cfg.get("bundleId", "")):
        out.append(f("CONFIG", "error", "project.config.json", "bundleId invalid or still a placeholder"))
    if not re.match(r"^\d+\.\d+\.\d+$", cfg.get("version", "")):
        out.append(f("CONFIG", "error", "project.config.json", "version must be semver"))
    if "__" in text:
        out.append(f("CONFIG", "error", "project.config.json", "unreplaced __TOKEN__ placeholder"))
    return out


def run(project, gates="qa/gates.json"):
    out = check_manifest(project) + check_ignore_file(project) + check_config(project)
    if not os.path.isfile(os.path.join(project, "Packages", "packages-lock.json")):
        out.append(f("LOCK-MISSING", "error", "Packages/packages-lock.json", "lock file missing (reproducible builds need it committed)"))
    elif os.path.exists(os.path.join(project, ".git")) and ignored(project, "Packages/packages-lock.json"):
        out.append(f("LOCK-MISSING", "error", "Packages/packages-lock.json", "lock file is ignored by git"))
    if os.path.isdir(os.path.join(project, ".git")) and ignored(project, "ProjectSettings/ProjectVersion.txt"):
        out.append(f("VERSION-IGNORED", "error", "ProjectSettings/ProjectVersion.txt", "must be tracked so local batch runner picks the right Editor"))
    files = tracked_files(project)
    for t in files or []:
        if SECRET_RE.search(t):
            out.append(f("SECRET-TRACKED", "error", t, "secret-bearing file is tracked; remove from the index (needs the user's approval) and rotate if it was pushed"))
    g = os.path.join(project, gates)
    gt = read(g)
    if gt is None:
        out.append(f("GATES", "warn", gates, "gates file not found"))
    else:
        try:
            json.loads(gt)
        except ValueError:
            out.append(f("GATES", "warn", gates, "not valid JSON"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--gates", default="qa/gates.json")
    a = ap.parse_args(argv)
    found = run(a.project, a.gates)
    for x in found:
        print("%s %s %s %s" % (x["severity"].upper(), x["rule"], x["file"], x["msg"]))
    errors = sum(1 for x in found if x["severity"] == "error")
    print("%d error(s), %d warning(s)" % (errors, len(found) - errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
