"""PreToolUse hook for Edit|Write|MultiEdit: protect files that agents must not change.

Denies (exit 2): keystores and signing/credential files, Unity YAML written by hand (.unity, .prefab, .meta, .asset:
use the Unity MCP / editor tools), package manifests and ProjectSettings unless the user allowed it by creating
`docs/pipeline/allow-settings-edits` , AGENTS.md and docs/feedback-notes.md overwrites (append-only: use Edit, not Write).
Everything else passes. Reasons are written to stderr so the agent can adapt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hooklib  # noqa: E402

SECRET_SUFFIX = (".keystore", ".jks", ".p12", ".pfx", ".pem")
SECRET_NAMES = ("google-services.json", "GoogleService-Info.plist")
UNITY_YAML = (".unity", ".prefab", ".meta", ".asset", ".mat", ".controller", ".anim")
APPEND_ONLY = ("agents.md", "docs/feedback-notes.md")


def decide(event):
    ti = event.get("tool_input") or {}
    path = hooklib.norm(ti.get("file_path") or ti.get("path") or "")
    if not path:
        return None
    low = path.lower()
    base = low.rsplit("/", 1)[-1]
    if low.endswith(SECRET_SUFFIX) or base in {n.lower() for n in SECRET_NAMES}:
        return "%s is a secret/signing file: never edited or printed by agents. Ask the user." % path
    if low.endswith(UNITY_YAML) and "/assets/" in "/" + low.lstrip("/") + "/" or low.endswith((".unity", ".prefab", ".meta")):
        return "%s is Unity YAML: do not hand-write it. Use Unity MCP / an idempotent editor tool (rule-editor-tool-safety)." % path
    allow = os.path.join(hooklib.project_dir(event), "docs", "pipeline", "allow-settings-edits")
    if ("/projectsettings/" in "/" + low or low.endswith("packages/manifest.json") or low.endswith("packages-lock.json")) and not os.path.exists(allow):
        return "%s is project configuration: ask the user first (create docs/pipeline/allow-settings-edits to allow)." % path
    if event.get("tool_name") == "Write" and any(low.endswith(a) for a in APPEND_ONLY) and os.path.exists(path):
        return "%s is append-only: use Edit to add lines, never overwrite it (parallel-agent rule)." % path
    return None


def main():
    event = hooklib.read_event()
    reason = decide(event)
    return hooklib.block(reason) if reason else 0


if __name__ == "__main__":
    sys.exit(main())
