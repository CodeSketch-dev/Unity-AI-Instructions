import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, LINT)

import engine  # noqa: E402

RULE = engine.Rule(
    id="demo-rule",
    pattern=r"BadCall\(",
    why="BadCall allocates every frame.",
    skill="demo-skill",
)
CS = os.path.join("Assets", "_Game", "Scripts", "Logic", "Thing.cs")


class EngineTests(unittest.TestCase):
    def test_match_gives_micro_prompt_with_skill_path_and_line(self):
        v = engine.lint_text(CS, "int a;\nBadCall(1);\n", rules=[RULE])
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0].line, 2)
        self.assertIn("[RULE demo-rule]", v[0].message)
        self.assertIn(".claude/skills/demo-skill/SKILL.md", v[0].message)
        self.assertIn("MANDATORY", v[0].message)
        self.assertLess(len(v[0].message), 400)

    def test_lint_ok_comment_suppresses(self):
        v = engine.lint_text(CS, "BadCall(1); // lint-ok:demo-rule one-time bootstrap\n", rules=[RULE])
        self.assertEqual(v, [])

    def test_editor_and_tests_paths_are_excluded(self):
        for p in (os.path.join("Assets", "Editor", "X.cs"), os.path.join("Assets", "Tests", "X.cs")):
            self.assertEqual(engine.lint_text(p, "BadCall(1);\n", rules=[RULE]), [])

    def test_vendor_and_reference_paths_are_excluded(self):
        for vendor in (("Packages", "com.x", "Runtime"), ("Assets", "Plugins", "Lib"), ("ReferenceSource~", "Demo", "Assets")):
            path = os.path.join(*vendor, "Thing.cs")
            self.assertEqual(engine.lint_text(path, "BadCall(1);" + chr(10), rules=[RULE]), [], path)

    def test_other_file_types_ignored(self):
        self.assertEqual(engine.lint_text("notes.txt", "BadCall(1);\n", rules=[RULE]), [])

    def test_cli_exit_2_on_violation_and_0_when_clean_or_engine_error(self):
        bad = os.path.join(HERE, "fixtures", "tmp_bad.cs")
        good = os.path.join(HERE, "fixtures", "tmp_good.cs")
        with open(bad, "w") as f:
            f.write("class A { void U(){ var g = new GameObject(\"Mgr\"); g.AddComponent<Mgr>(); } }\n")
        with open(good, "w") as f:
            f.write("class A { }\n")
        run = lambda *a: subprocess.run([sys.executable, os.path.join(LINT, "run_lint.py"), *a], capture_output=True, text=True)
        try:
            r = run(bad)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("[RULE no-runtime-manager-gameobject]", r.stdout + r.stderr)
            self.assertEqual(run(good).returncode, 0)
            self.assertEqual(run(os.path.join(HERE, "fixtures", "missing.cs")).returncode, 0)
        finally:
            os.remove(bad)
            os.remove(good)


if __name__ == "__main__":
    unittest.main()


class HookAndInstallTests(unittest.TestCase):
    BAD = "class A { void U(){ var g = new GameObject(\"Mgr\"); g.AddComponent<Mgr>(); } }\n"

    def _run(self, args, stdin=None, cwd=None):
        return subprocess.run([sys.executable, os.path.join(LINT, "run_lint.py"), *args], input=stdin, capture_output=True, text=True, cwd=cwd)

    def test_hook_mode_reads_file_path_from_tool_json_and_matches_direct_output(self):
        import json
        import tempfile
        d = tempfile.mkdtemp()
        f = os.path.join(d, "Mgr.cs")
        open(f, "w").write(self.BAD)
        payload = json.dumps({"tool_input": {"file_path": f}})
        hook = self._run(["--hook"], stdin=payload)
        direct = self._run([f])
        self.assertEqual(hook.returncode, 2)
        self.assertEqual(hook.stderr, direct.stderr)
        txt = os.path.join(d, "a.txt")
        open(txt, "w").write(self.BAD)
        self.assertEqual(self._run(["--hook"], stdin=json.dumps({"tool_input": {"file_path": txt}})).returncode, 0)
        self.assertEqual(self._run(["--hook"], stdin="not json").returncode, 0)

    def test_changed_mode_matches_direct_output(self):
        import tempfile
        d = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=d)
        open(os.path.join(d, "Mgr.cs"), "w").write(self.BAD)
        ch = self._run(["--changed"], cwd=d)
        direct = self._run(["Mgr.cs"], cwd=d)
        self.assertEqual(ch.returncode, 2)
        self.assertEqual(ch.stderr, direct.stderr)

    def test_install_script_copies_lint_and_registers_hook_idempotently(self):
        import json
        import tempfile
        repo = os.path.abspath(os.path.join(LINT, "..", ".."))
        proj = tempfile.mkdtemp()
        ps1 = os.path.join(repo, "tools", "sync", "install_project_lint.ps1")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, "-Repo", repo, "-Project", proj]
        for _ in range(2):
            r = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.isfile(os.path.join(proj, ".claude", "lint", "run_lint.py")))
        self.assertTrue(os.path.isfile(os.path.join(proj, ".claude", "lint", "rules", "no_runtime_manager_gameobject.py")))
        self.assertFalse(os.path.exists(os.path.join(proj, ".claude", "lint", "tests")))
        s = json.load(open(os.path.join(proj, ".claude", "settings.local.json"), encoding="utf-8"))
        cmds = [h["command"] for e in s["hooks"]["PostToolUse"] for h in e["hooks"] if "run_lint.py" in h["command"]]
        self.assertEqual(len(cmds), 1)
        self.assertIn("--hook", cmds[0])


class ReviewFixTests(unittest.TestCase):
    BAD = "class A { void U(){ var g = new GameObject(\"Mgr\"); g.AddComponent<Mgr>(); } }\n"

    def test_changed_mode_finds_cs_inside_new_untracked_folder_and_in_project_subfolder(self):
        import tempfile
        top = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=top)
        proj = os.path.join(top, "UnityProj")
        os.makedirs(os.path.join(proj, "Assets", "NewDir"))
        open(os.path.join(proj, "Assets", "NewDir", "Mgr.cs"), "w").write(self.BAD)
        r = subprocess.run([sys.executable, os.path.join(LINT, "run_lint.py"), "--changed"], capture_output=True, text=True, cwd=proj)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Mgr.cs:1:", r.stderr)

    def test_comment_lines_are_not_flagged(self):
        src = "// var g = new GameObject(\"x\"); g.AddComponent<Mgr>();\n/// new GameObject(\"y\") AddComponent<Z>\n"
        self.assertEqual(engine.lint_text(CS, src), [])

    def test_hook_mode_reads_utf8_stdin(self):
        import json
        import tempfile
        d = tempfile.mkdtemp()
        f = os.path.join(d, "Tenđẹp.cs")
        open(f, "w", encoding="utf-8").write(self.BAD)
        payload = json.dumps({"tool_input": {"file_path": f}}, ensure_ascii=False).encode("utf-8")
        r = subprocess.run([sys.executable, os.path.join(LINT, "run_lint.py"), "--hook"], input=payload, capture_output=True)
        self.assertEqual(r.returncode, 2, r.stderr)
