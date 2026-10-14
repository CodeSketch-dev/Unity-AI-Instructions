"""Print (and with --yes run) the batch-mode Unity build command for an Android AAB/APK. Never signs from files in the repo.

  py -I build_cmd.py --project P --version 1.2.0 --number 57 [--apk] [--development] [--out Builds] [--yes]

Uses the Editor pinned in ProjectSettings/ProjectVersion.txt (never another version: that upgrades the project) and refuses if
an Editor holds the project (Temp/UnityLockfile): build from a separate worktree or close the Editor. Signing values come from
the environment (KEYSTORE_PATH, KEYSTORE_PASS, KEY_ALIAS, KEY_PASS) read by BuildCli inside Unity; this script only checks that
they are set and never prints them. Exit codes: 0 ok, 1 build failed, 2 blocked.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "qa-batch-and-fallbacks", "scripts"))
import qa_unity_batch as batch  # noqa: E402

SIGNING_VARS = ("KEYSTORE_PATH", "KEYSTORE_PASS", "KEY_ALIAS", "KEY_PASS")


def build_command(editor, project, method, version, number, out, development, log):
    cmd = [editor, "-batchmode", "-nographics", "-quit", "-projectPath", project, "-buildTarget", "Android", "-logFile", log,
           "-executeMethod", method, "-buildVersion", version, "-buildNumber", str(number), "-outputDir", out]
    if development:
        cmd.append("-development")
    return cmd


def missing_signing(env):
    return [v for v in SIGNING_VARS if not env.get(v)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--version", required=True)
    ap.add_argument("--number", required=True, type=int)
    ap.add_argument("--apk", action="store_true")
    ap.add_argument("--development", action="store_true")
    ap.add_argument("--out", default="Builds")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    ver = batch.pinned_version(a.project)
    editor = batch.find_editor(ver) if ver else None
    if not editor:
        print("blocked: pinned Editor %s not installed (do not use another version; ask the user)" % ver)
        return 2
    if batch.editor_running(a.project):
        print("blocked: Temp/UnityLockfile exists; build from a separate worktree or close the Editor")
        return 2
    release_signing = not a.development and not a.apk
    if release_signing and missing_signing(os.environ):
        print("blocked: set %s in the environment (the human provides them; they are never printed or stored)" % ", ".join(missing_signing(os.environ)))
        return 2
    os.makedirs(os.path.join(a.project, "Logs"), exist_ok=True)
    method = "Game.EditorTools.BuildCli." + ("BuildAndroidApk" if a.apk else "BuildAndroidAab")
    cmd = build_command(editor, a.project, method, a.version, a.number, a.out, a.development, os.path.join("Logs", "build.log"))
    print(" ".join('"%s"' % c if " " in c else c for c in cmd))
    if not a.yes:
        print("not run: pass --yes to start the build")
        return 0
    rc = subprocess.run(cmd, timeout=7200).returncode
    print("exit code %d (0 ok, 1 build error, other: Unity crash or license; read Logs/build.log with unity-log-triage)" % rc)
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
