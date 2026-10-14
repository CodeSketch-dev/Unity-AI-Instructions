"""PostToolUse hook for Edit|Write on Unity files: run the cheap static checks on that one file (exit 2 feeds errors back).

C# under the first-party folder -> banned-API and EditorLeak checks. .prefab/.unity/.asset/.mat -> missing script/reference scan.
Silent when the project is not a Unity project, the file is outside Assets/, or nothing hard is found. Warnings are never printed
(token cost); run qa_run.py static for them.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hooklib  # noqa: E402

CANDIDATES = [
    os.environ.get("QA_STATIC_SCRIPTS", ""),
    os.path.join(HERE, "..", "..", "skills", "qa-static-checks", "scripts"),                # repo or plugin layout
    os.path.join(os.path.expanduser("~"), ".claude", "skills", "qa-static-checks", "scripts"),  # synced user-level install
]


def scripts_dir():
    return next((c for c in CANDIDATES if c and os.path.isfile(os.path.join(c, "qa_banned_api.py"))), None)


def check(project, rel_path):
    sd = scripts_dir()
    if not sd:
        return []
    sys.path.insert(0, sd)
    import qa_asmdef
    import qa_banned_api
    import qa_scan_refs
    low = rel_path.lower()
    found = []
    if low.endswith(".cs"):
        found += qa_banned_api.scan(project, [rel_path])
        found += [f for f in qa_asmdef.scan(project, [rel_path]) if f["rule"] == "EDITOR-LEAK"]
    elif low.endswith((".prefab", ".unity", ".asset", ".mat")):
        found += qa_scan_refs.scan(project, [rel_path])[0]
    return [f for f in found if f["severity"] == "error"]


def main():
    event = hooklib.read_event()
    project = hooklib.project_dir(event)
    if not os.path.isdir(os.path.join(project, "ProjectSettings")):
        return 0
    path = hooklib.norm((event.get("tool_input") or {}).get("file_path", ""))
    if not path:
        return 0
    rel = os.path.relpath(path, project).replace("\\", "/") if os.path.isabs(path) else path
    if not rel.startswith("Assets/"):
        return 0
    try:
        errors = check(project, rel)
    except Exception as e:  # a broken checker must never block editing
        sys.stderr.write("qa_post_edit skipped: %s\n" % e)
        return 0
    if not errors:
        return 0
    lines = ["%s %s:%s %s" % (f["rule"], f["file"], f["line"], f["msg"]) for f in errors[:8]]
    return hooklib.block("static QA found %d hard issue(s) in the file you just edited:\n%s" % (len(errors), "\n".join(lines)))


if __name__ == "__main__":
    sys.exit(main())
