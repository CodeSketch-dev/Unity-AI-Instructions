"""Run Unity headless (compile / EditMode / PlayMode tests) and parse the NUnit result. Stdlib only.

  py -I qa_unity_batch.py plan  --project P [--platform EditMode|PlayMode] [--filter Qa_]     # print the command, run nothing
  py -I qa_unity_batch.py run   --project P [--platform EditMode] [--filter Qa_] [--yes]
  py -I qa_unity_batch.py parse --results results.xml

Refuses when: the pinned Editor (ProjectSettings/ProjectVersion.txt) is not installed (never opens a project with another
version: that upgrades it), or an Editor already holds the project (Temp/UnityLockfile). Exit 0 = tests green.
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def pinned_version(project):
    try:
        with open(os.path.join(project, "ProjectSettings", "ProjectVersion.txt"), encoding="utf-8") as f:
            m = re.search(r"m_EditorVersion:\s*(\S+)", f.read())
        return m.group(1) if m else None
    except OSError:
        return None


def find_editor(version):
    roots = [os.environ.get("UNITY_HUB_EDITORS", ""), r"C:\Program Files\Unity\Hub\Editor", "/Applications/Unity/Hub/Editor"]
    for r in roots:
        if not r:
            continue
        for exe in (os.path.join(r, version, "Editor", "Unity.exe"), os.path.join(r, version, "Unity.app", "Contents", "MacOS", "Unity")):
            if os.path.isfile(exe):
                return exe
    return None


def editor_running(project):
    """A live Editor keeps Temp/UnityLockfile open; a stale file from a crash is removable, so we only warn on its presence."""
    return os.path.isfile(os.path.join(project, "Temp", "UnityLockfile"))


def build_command(editor, project, platform, filt, results, log):
    cmd = [editor, "-batchmode", "-projectPath", project, "-runTests", "-testPlatform", platform, "-testResults", results, "-logFile", log]
    if filt:
        cmd += ["-testFilter", filt]
    return cmd


def parse_results(path):
    """Return (passed, failed, skipped, [failed test names with first message line])."""
    root = ET.parse(path).getroot()
    passed = failed = skipped = 0
    fails = []
    for tc in root.iter("test-case"):
        r = (tc.get("result") or "").lower()
        if r == "passed":
            passed += 1
        elif r in ("skipped", "ignored", "inconclusive"):
            skipped += 1
        else:
            failed += 1
            msg = tc.find("failure/message")
            first = (msg.text or "").strip().splitlines()[0] if msg is not None and msg.text else ""
            fails.append("%s: %s" % (tc.get("fullname") or tc.get("name"), first[:160]))
    return passed, failed, skipped, fails


def prepare(a):
    ver = pinned_version(a.project)
    if not ver:
        print("blocked: no ProjectSettings/ProjectVersion.txt")
        return None
    ed = find_editor(ver)
    if not ed:
        print("blocked: Editor %s is not installed; do not open the project with another version (ask the user)" % ver)
        return None
    if editor_running(a.project):
        print("blocked: Temp/UnityLockfile exists; an Editor probably holds the project. Use MCP, or close the Editor first")
        return None
    out = os.path.join(a.project, "docs", "qa", "artifacts")
    os.makedirs(out, exist_ok=True)
    res = os.path.join(out, "results-%s.xml" % a.platform)
    log = os.path.join(out, "unity-%s.log" % a.platform)
    return build_command(ed, a.project, a.platform, a.filter, res, log), res, log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "run", "parse"])
    ap.add_argument("--project", default=".")
    ap.add_argument("--platform", default="EditMode", choices=["EditMode", "PlayMode"])
    ap.add_argument("--filter", default="")
    ap.add_argument("--results")
    ap.add_argument("--yes", action="store_true", help="confirm running Unity")
    a = ap.parse_args(argv)
    if a.mode == "parse":
        p, f, s, fails = parse_results(a.results)
        print("passed %d, failed %d, skipped %d" % (p, f, s))
        for x in fails:
            print("FAIL " + x)
        return 1 if f else 0
    prep = prepare(a)
    if not prep:
        return 2
    cmd, res, log = prep
    print(" ".join('"%s"' % c if " " in c else c for c in cmd))
    if a.mode == "plan":
        return 0
    if not a.yes:
        print("not run: pass --yes to start Unity")
        return 2
    subprocess.run(cmd, timeout=3600)
    if not os.path.isfile(res):
        print("no results file; read the log summary: py -I summarize_unity_log.py %s" % log)
        return 1
    p, f, s, fails = parse_results(res)
    print("passed %d, failed %d, skipped %d" % (p, f, s))
    for x in fails[:20]:
        print("FAIL " + x)
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
