import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(HERE, "..", "..", "hooks", "scripts")
sys.path.insert(0, HOOKS)

import protect_files  # noqa: E402
import block_git_danger  # noqa: E402
import stop_gate  # noqa: E402
import gate_ok  # noqa: E402


def run(script, event, project, extra_env=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project, **(extra_env or {}))
    return subprocess.run([sys.executable, "-I", os.path.join(HOOKS, script)], input=json.dumps(event), capture_output=True,
                          text=True, env=env, timeout=30)


class ProtectTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def ev(self, path, tool="Edit"):
        return {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": self.d}

    def test_secrets_blocked(self):
        for p in ("C:/x/Upstore/user.keystore", "app/google-services.json", "a/b.jks"):
            self.assertIsNotNone(protect_files.decide(self.ev(p)), p)

    def test_unity_yaml_blocked_but_cs_allowed(self):
        self.assertIsNotNone(protect_files.decide(self.ev("Assets/_Game/Scenes/Game.unity")))
        self.assertIsNotNone(protect_files.decide(self.ev("Assets/_Game/Prefabs/Popup.prefab")))
        self.assertIsNotNone(protect_files.decide(self.ev("Assets/_Game/Scripts/A.cs.meta")))
        self.assertIsNone(protect_files.decide(self.ev("Assets/_Game/Scripts/A.cs")))

    def test_settings_need_permission(self):
        self.assertIsNotNone(protect_files.decide(self.ev("ProjectSettings/ProjectSettings.asset")))
        self.assertIsNotNone(protect_files.decide(self.ev("Packages/manifest.json")))
        os.makedirs(os.path.join(self.d, "docs", "pipeline"))
        open(os.path.join(self.d, "docs", "pipeline", "allow-settings-edits"), "w").close()
        env = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = self.d
        try:
            self.assertIsNone(protect_files.decide(self.ev("Packages/manifest.json")))
        finally:
            if env is None:
                del os.environ["CLAUDE_PROJECT_DIR"]
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = env

    def test_append_only_docs_cannot_be_overwritten(self):
        p = os.path.join(self.d, "docs", "feedback-notes.md")
        os.makedirs(os.path.dirname(p))
        open(p, "w").write("x")
        self.assertIsNotNone(protect_files.decide(self.ev(p, "Write")))
        self.assertIsNone(protect_files.decide(self.ev(p, "Edit")))

    def test_process_exit_codes(self):
        self.assertEqual(run("protect_files.py", self.ev("Assets/A.unity"), self.d).returncode, 2)
        r = run("protect_files.py", self.ev("Assets/A.cs"), self.d)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(run("protect_files.py", {}, self.d).returncode, 0)
        self.assertIn("Unity YAML", run("protect_files.py", self.ev("x.prefab"), self.d).stderr)


class GitTests(unittest.TestCase):
    def cmd(self, c):
        return block_git_danger.decide({"tool_input": {"command": c}, "cwd": tempfile.gettempdir()})

    def test_dangerous_blocked(self):
        for c in ("git push origin main", "git push --force", "git reset --hard HEAD~1", "git clean -fd", "git checkout -- Assets/A.cs",
                  "git restore .", "git stash drop", "git branch -D x", "rm -rf Assets/_Game"):
            self.assertIsNotNone(self.cmd(c), c)

    def test_safe_allowed(self):
        for c in ("git status", "git diff --stat", "git log -5", "git add -A", "git commit -m x", "ls", "py -I tools/skill_lint.py skills"):
            self.assertIsNone(self.cmd(c), c)

    def test_commits_can_be_disabled(self):
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, "docs", "pipeline"))
            open(os.path.join(d, "docs", "pipeline", "no-commits"), "w").close()
            self.assertIsNotNone(block_git_danger.decide({"tool_input": {"command": "git commit -m x"}, "cwd": d}))
        finally:
            shutil.rmtree(d)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def dirty(self):
        return os.path.join(self.d, "docs", "pipeline", "run-state", "dirty.txt")

    def test_mark_dirty_tracks_unity_files_only(self):
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/_Game/A.cs"}}, self.d)
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/_Game/A.cs"}}, self.d)
        run("mark_dirty.py", {"tool_input": {"file_path": "docs/readme.md"}}, self.d)
        with open(self.dirty(), encoding="utf-8") as f:
            self.assertEqual(f.read().split(), ["Assets/_Game/A.cs"])

    def test_stop_gate_blocks_until_evidence_then_passes(self):
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/A.cs"}}, self.d)
        r = run("stop_gate.py", {}, self.d)
        self.assertEqual(r.returncode, 2)
        self.assertIn("gate_ok.py", r.stderr)
        self.assertEqual(gate_ok.main(["--project", self.d]), 1)                       # empty evidence refused
        self.assertEqual(gate_ok.main(["--project", self.d, "--evidence", "Console clean"]), 0)
        self.assertEqual(run("stop_gate.py", {}, self.d).returncode, 0)
        self.assertFalse(os.path.exists(self.dirty()))

    def test_stop_gate_gives_up_after_three_blocks_and_writes_handoff(self):
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/A.cs"}}, self.d)
        codes = [run("stop_gate.py", {}, self.d).returncode for _ in range(4)]
        self.assertEqual(codes, [2, 2, 2, 0])
        with open(os.path.join(self.d, "docs", "agent-handoff.md"), encoding="utf-8") as f:
            self.assertIn("never verified", f.read())

    def test_stop_gate_can_be_disabled(self):
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/A.cs"}}, self.d)
        self.assertEqual(run("stop_gate.py", {}, self.d, {"UNITY_GATE_DISABLE": "1"}).returncode, 0)

    def test_session_start_prints_context(self):
        os.makedirs(os.path.join(self.d, "docs"))
        with open(os.path.join(self.d, "docs", "agent-handoff.md"), "w", encoding="utf-8") as f:
            f.write("# Handoff\n- 2026 | agent | did x\n")
        run("mark_dirty.py", {"tool_input": {"file_path": "Assets/A.cs"}}, self.d)
        r = run("session_start.py", {}, self.d)
        self.assertEqual(r.returncode, 0)
        self.assertIn("did x", r.stdout)
        self.assertIn("never verified", r.stdout)

    def test_precompact_note_needs_state(self):
        self.assertEqual(run("precompact_note.py", {}, self.d).returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs", "orchestrator", "log.md")))
        os.makedirs(os.path.join(self.d, "docs", "orchestrator"))
        with open(os.path.join(self.d, "docs", "orchestrator", "state.json"), "w", encoding="utf-8") as f:
            json.dump({"phase": 2, "tasks": {"T1": {"status": "in_progress"}}}, f)
        run("precompact_note.py", {}, self.d)
        with open(os.path.join(self.d, "docs", "orchestrator", "log.md"), encoding="utf-8") as f:
            self.assertIn("T1", f.read())


class ManifestTests(unittest.TestCase):
    def test_hooks_json_references_existing_scripts(self):
        path = os.path.join(HERE, "..", "..", "hooks", "hooks.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        import re
        cmds = [h["command"] for ev in data["hooks"].values() for entry in ev for h in entry["hooks"]]
        self.assertGreaterEqual(len(cmds), 7)
        for c in cmds:
            m = re.search(r"hooks/scripts/(\w+\.py)", c)
            self.assertTrue(m and os.path.isfile(os.path.join(HOOKS, m.group(1))), c)
        self.assertEqual(sorted(data["hooks"]), ["PostToolUse", "PreCompact", "PreToolUse", "SessionStart", "Stop"])


if __name__ == "__main__":
    unittest.main()
