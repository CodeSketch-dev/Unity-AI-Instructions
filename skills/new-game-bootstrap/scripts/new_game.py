"""Turn a fresh copy of the game template into a new game (text replacement + stubs, never ProjectSettings YAML).

  py -I new_game.py --project P --config P/project.config.json [--dry-run] [--template-marker game-template-unity]

project.config.json: {"company": "...", "product": "...", "bundleId": "com.company.game", "version": "0.1.0",
                      "unity": "6000.3.22f1", "orientation": "portrait", "rootNamespace": "Game"}

What it does
  - validates the config (bundle id, semver, Unity version matches ProjectVersion.txt when present)
  - replaces __PRODUCT__ / __COMPANY__ / __BUNDLE_ID__ / __VERSION__ / __NAMESPACE__ tokens in known text files
  - writes docs/project-setup.md, docs/feedback-notes.md and docs/agent-handoff.md stubs when missing
  - prints the human TODO list (SDK keys, keystore, icon, store listing)
ProjectSettings values are applied by the Editor script BuildSettingsApplier (Bootstrap), not by editing YAML here.
Refuses to run when the git remote still points at the template, or the tree is dirty, so the template is never rewritten.
"""
import argparse
import json
import os
import re
import subprocess
import sys

TEXT_EXTS = (".cs", ".asmdef", ".json", ".md", ".yml", ".yaml", ".txt", ".ps1", ".py", ".gradle", ".xml", ".properties")
SKIP_DIRS = {"Library", "Temp", "obj", "Logs", "Builds", ".git", "UserSettings"}
BUNDLE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){2,}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
NS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
TODO = [
    "Provide the SDK keys file from secrets.example.json (real values stay untracked)",
    "Generate the upload keystore yourself (keytool); keep it outside the repo and back it up before the first upload",
    "Replace the placeholder icon and splash",
    "Create the store listing and fill docs/store/",
    "Decide ads/analytics SDK defines (USE_MAX, USE_ADJUST, ...) in project.config.json",
]


def validate(cfg, project):
    errs = []
    for k in ("company", "product", "bundleId", "version"):
        if not cfg.get(k):
            errs.append("missing " + k)
    if cfg.get("bundleId") and not BUNDLE_RE.match(cfg["bundleId"]):
        errs.append("bundleId must look like com.company.game (lowercase, 3+ segments)")
    if cfg.get("version") and not SEMVER_RE.match(cfg["version"]):
        errs.append("version must be semver x.y.z")
    if not NS_RE.match(cfg.get("rootNamespace", "Game")):
        errs.append("rootNamespace is not a valid C# namespace")
    if cfg.get("orientation", "portrait") not in ("portrait", "landscape", "auto"):
        errs.append("orientation must be portrait, landscape or auto")
    pv = os.path.join(project, "ProjectSettings", "ProjectVersion.txt")
    if cfg.get("unity") and os.path.isfile(pv):
        with open(pv, encoding="utf-8") as f:
            m = re.search(r"m_EditorVersion:\s*(\S+)", f.read())
        if m and m.group(1) != cfg["unity"]:
            errs.append("config unity %s differs from ProjectVersion.txt %s" % (cfg["unity"], m.group(1)))
    return errs


def git_state(project, marker):
    """Return an error string or None. No git repo at all is fine (fresh export)."""
    if not os.path.exists(os.path.join(project, ".git")):
        return None
    try:
        remote = subprocess.run(["git", "-C", project, "remote", "-v"], capture_output=True, text=True, timeout=20)
        if remote.returncode != 0:
            return None
        if marker and marker in remote.stdout:
            return "git remote still points at the template (%s); re-init the repository first" % marker
        status = subprocess.run(["git", "-C", project, "status", "--porcelain"], capture_output=True, text=True, timeout=20).stdout
        if status.strip():
            return "working tree is dirty; commit or stash first (this tool never runs on unsaved work)"
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def replace_tokens(project, cfg, dry_run):
    tokens = {"__PRODUCT__": cfg["product"], "__COMPANY__": cfg["company"], "__BUNDLE_ID__": cfg["bundleId"],
              "__VERSION__": cfg["version"], "__NAMESPACE__": cfg.get("rootNamespace", "Game")}
    changed = []
    for dp, dn, fn in os.walk(project):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for n in fn:
            if not n.lower().endswith(TEXT_EXTS):
                continue
            p = os.path.join(dp, n)
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            new = text
            for k, v in tokens.items():
                new = new.replace(k, v)
            if new != text:
                changed.append(os.path.relpath(p, project).replace("\\", "/"))
                if not dry_run:
                    with open(p, "w", encoding="utf-8", newline="\n") as f:
                        f.write(new)
    return changed


def write_stubs(project, cfg, dry_run):
    made = []
    stubs = {
        "docs/project-setup.md": "# Project setup\n\nProduct: %s\nBundle id: %s\nUnity: %s\nOrientation: %s\n\nDecisions are appended here by the bootstrap and later agents.\n"
        % (cfg["product"], cfg["bundleId"], cfg.get("unity", "?"), cfg.get("orientation", "portrait")),
        "docs/feedback-notes.md": "# Feedback notes\n\nAppend dated bullets grouped by topic. Re-read before appending.\n",
        "docs/agent-handoff.md": "# Agent handoff\n\nAppend-only. One line per finished task: date | agent | files | what changed | what to re-read.\n",
    }
    for rel_path, body in stubs.items():
        p = os.path.join(project, rel_path)
        if os.path.exists(p):
            continue
        made.append(rel_path)
        if not dry_run:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(body)
    return made


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--config", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--template-marker", default="game-template-unity")
    a = ap.parse_args(argv)
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    errs = validate(cfg, a.project)
    if errs:
        for e in errs:
            print("config error: " + e)
        return 1
    blocked = git_state(a.project, a.template_marker)
    if blocked:
        print("blocked: " + blocked)
        return 2
    changed = replace_tokens(a.project, cfg, a.dry_run)
    made = write_stubs(a.project, cfg, a.dry_run)
    print("%s%d file(s) updated, %d stub(s) written" % ("[dry run] " if a.dry_run else "", len(changed), len(made)))
    for c in changed[:30]:
        print("  updated " + c)
    print("Next, in Unity (batch or MCP): BuildCli.Bootstrap applies ProjectSettings from project.config.json")
    print("TODO for the human:")
    for t in TODO:
        print("  - " + t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
