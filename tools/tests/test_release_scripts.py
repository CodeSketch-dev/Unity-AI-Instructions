import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills")
sys.path.insert(0, os.path.join(SK, "new-game-bootstrap", "scripts"))
sys.path.insert(0, os.path.join(SK, "unity-batch-build", "scripts"))

import build_cmd  # noqa: E402
try:
    import create_pilot  # noqa: E402
except ImportError:
    create_pilot = None
import new_game  # noqa: E402
import project_preflight  # noqa: E402
import size_report  # noqa: E402

GOOD_CFG = {"company": "Acme", "product": "Sky Climb", "bundleId": "com.acme.skyclimb", "version": "0.1.0", "unity": "6000.3.22f1"}


class Proj(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def w(self, rel, text):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return p

    def git(self, *a):
        return subprocess.run(["git", "-C", self.d] + list(a), capture_output=True, text=True)


class NewGameTests(Proj):
    def test_validate(self):
        self.assertEqual(new_game.validate(GOOD_CFG, self.d), [])
        self.assertTrue(new_game.validate(dict(GOOD_CFG, bundleId="Com.Bad"), self.d))
        self.assertTrue(new_game.validate(dict(GOOD_CFG, version="1.0"), self.d))
        self.assertTrue(new_game.validate({}, self.d))
        self.w("ProjectSettings/ProjectVersion.txt", "m_EditorVersion: 2022.3.62f3\n")
        self.assertTrue(any("ProjectVersion" in e for e in new_game.validate(GOOD_CFG, self.d)))

    def test_replace_and_stubs(self):
        self.w("Assets/_Game/Scripts/Core/Info.cs", 'namespace __NAMESPACE__ { class Info { const string ID = "__BUNDLE_ID__"; } }')
        self.w("Assets/_Game/Art/x.png", "__PRODUCT__")
        self.w("Library/skip.cs", "__PRODUCT__")
        cfg = self.w("project.config.json", json.dumps(GOOD_CFG))
        rc = new_game.main(["--project", self.d, "--config", cfg, "--template-marker", ""])
        self.assertEqual(rc, 0)
        text = open(os.path.join(self.d, "Assets/_Game/Scripts/Core/Info.cs"), encoding="utf-8").read()
        self.assertIn("namespace Game", text)
        self.assertIn("com.acme.skyclimb", text)
        self.assertEqual(open(os.path.join(self.d, "Assets/_Game/Art/x.png")).read(), "__PRODUCT__")   # binary-ish ext untouched
        self.assertEqual(open(os.path.join(self.d, "Library/skip.cs")).read(), "__PRODUCT__")
        for stub in ("docs/project-setup.md", "docs/feedback-notes.md", "docs/agent-handoff.md"):
            self.assertTrue(os.path.isfile(os.path.join(self.d, stub)))

    def test_dry_run_changes_nothing(self):
        p = self.w("Assets/A.cs", "// __PRODUCT__")
        cfg = self.w("c.json", json.dumps(GOOD_CFG))
        new_game.main(["--project", self.d, "--config", cfg, "--dry-run", "--template-marker", ""])
        self.assertEqual(open(p).read(), "// __PRODUCT__")
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs", "project-setup.md")))

    def test_refuses_template_remote_and_dirty_tree(self):
        if self.git("init", "-q").returncode != 0:
            self.skipTest("git unavailable")
        self.git("remote", "add", "origin", "https://example.com/acme/game-template-unity.git")
        self.assertIn("template", new_game.git_state(self.d, "game-template-unity"))
        self.git("remote", "remove", "origin")
        self.w("Assets/A.cs", "x")
        self.assertIn("dirty", new_game.git_state(self.d, "game-template-unity"))


class PilotTemplateTests(Proj):
    def test_copier_dry_run_copies_template_and_refuses_nonempty_destination(self):
        self.assertIsNotNone(create_pilot)
        source = os.path.join(SK, "new-game-bootstrap", "assets", "game-template-unity")
        dest = os.path.join(self.d, "pilot")
        self.assertEqual(create_pilot.main(["--source", source, "--destination", dest, "--dry-run"]), 0)
        self.assertFalse(os.path.exists(dest))
        self.assertEqual(create_pilot.main(["--source", source, "--destination", dest]), 0)
        self.assertTrue(os.path.isfile(os.path.join(dest, "Packages", "manifest.json")))
        self.assertTrue(os.path.isfile(os.path.join(dest, "ProjectSettings", "ProjectVersion.txt")))
        self.w("occupied/x.txt", "x")
        self.assertEqual(create_pilot.main(["--source", source, "--destination", os.path.join(self.d, "occupied")]), 2)


class PreflightTests(Proj):
    def good_tree(self):
        self.w("Packages/manifest.json", json.dumps({"dependencies": {
            "com.sketchengine": "https://github.com/x/SketchEngine.git#v1.0.1", "com.unity.ugui": "2.0.0"}}))
        self.w("Packages/packages-lock.json", "{}")
        self.w("ProjectSettings/ProjectVersion.txt", "m_EditorVersion: 6000.3.22f1\n")
        gi = open(os.path.join(HERE, "..", "..", "skills", "new-game-bootstrap", "assets", "gitignore.template"), encoding="utf-8").read()
        self.w(".gitignore", gi)
        self.w("project.config.json", json.dumps(GOOD_CFG))
        self.w("qa/gates.json", "{}")

    def rules(self):
        return {x["rule"] for x in project_preflight.run(self.d) if x["severity"] == "error"}

    def test_good_tree_is_clean(self):
        self.good_tree()
        self.assertEqual(self.rules(), set())

    def test_unpinned_dependency(self):
        self.good_tree()
        self.w("Packages/manifest.json", json.dumps({"dependencies": {"com.codesketch": "https://github.com/x/CodeSketch.git#main",
                                                                      "a.b": "https://github.com/x/Y.git"}}))
        found = [x for x in project_preflight.run(self.d) if x["rule"] == "PKG-UNPINNED"]
        self.assertEqual(len(found), 2)

    def test_missing_lock_gitignore_and_config(self):
        self.good_tree()
        os.remove(os.path.join(self.d, "Packages", "packages-lock.json"))
        self.w(".gitignore", "Library/\n")
        self.w("project.config.json", json.dumps(dict(GOOD_CFG, bundleId="com.__BUNDLE__.x")))
        self.assertEqual(self.rules(), {"LOCK-MISSING", "IGNORE-MISSING", "CONFIG"})

    def test_tracked_secret(self):
        self.good_tree()
        if self.git("init", "-q").returncode != 0:
            self.skipTest("git unavailable")
        self.w("Upstore/app.keystore", "binary")
        self.git("add", "-f", "Upstore/app.keystore")
        found = [x for x in project_preflight.run(self.d) if x["rule"] == "SECRET-TRACKED"]
        self.assertEqual([x["file"] for x in found], ["Upstore/app.keystore"])


class SizeTests(Proj):
    def make_zip(self, name, payload):
        p = os.path.join(self.d, name)
        with zipfile.ZipFile(p, "w", zipfile.ZIP_STORED) as z:
            z.writestr("base/lib/arm64-v8a/libil2cpp.so", payload)
            z.writestr("base/assets/data.bundle", b"x" * 1024)
            z.writestr("BundleConfig.pb", b"y")
        return p

    def test_budget_and_regression(self):
        small = size_report.analyse(self.make_zip("a.aab", os.urandom(200000)))
        self.assertEqual(small["top"][0]["name"], "base/lib/arm64-v8a/libil2cpp.so")
        self.assertIn("native libs", small["groups_mb"])
        notes, failed = size_report.gate(small, {"size": {"max_mb": 1, "target_mb": 0.1}}, None)
        self.assertFalse(failed)
        self.assertTrue(any(n.startswith("WARN") for n in notes))
        notes, failed = size_report.gate(dict(small, size_mb=2.0), {"size": {"max_mb": 1}}, None)
        self.assertTrue(failed)
        notes, failed = size_report.gate(dict(small, size_mb=1.2), {"size": {"max_mb": 5, "max_regression_pct": 5}}, {"size_mb": 1.0})
        self.assertTrue(failed)
        notes, failed = size_report.gate(dict(small, size_mb=1.03), {"size": {"max_mb": 5, "max_regression_pct": 5}}, {"size_mb": 1.0})
        self.assertFalse(failed)

    def test_cli_writes_report(self):
        art = self.make_zip("b.aab", os.urandom(1000))
        out = os.path.join(self.d, "size.json")
        self.assertEqual(size_report.main(["--artifact", art, "--out", out]), 0)
        self.assertIn("gate", json.load(open(out)))


class BuildCmdTests(unittest.TestCase):
    def test_batch_build_assets_are_local_only(self):
        skill_root = os.path.join(SK, "unity-batch-build")
        skill_text = Path(skill_root, "SKILL.md").read_text(encoding="utf-8").lower()
        local_template = os.path.join(skill_root, "assets", "local-build.ps1.template")
        retired_template = os.path.join(skill_root, "assets", "ci" + ".yml.template")

        self.assertIn("local unity batch", skill_text)
        self.assertIn("no remote build service", skill_text)
        self.assertTrue(os.path.isfile(local_template))
        self.assertFalse(os.path.exists(retired_template))

        template_text = Path(local_template).read_text(encoding="utf-8").lower()
        self.assertIn("qa_unity_batch.py", template_text)
        self.assertIn("build_cmd.py", template_text)
        self.assertNotIn("github", template_text)
        self.assertNotIn("upload", template_text)

    def test_command_shape(self):
        cmd = build_cmd.build_command("U.exe", "P", "Game.EditorTools.BuildCli.BuildAndroidAab", "1.2.0", 57, "Builds", False, "Logs/b.log")
        self.assertIn("-executeMethod", cmd)
        self.assertEqual(cmd[cmd.index("-buildNumber") + 1], "57")
        self.assertNotIn("-development", cmd)
        self.assertTrue(all("PASS" not in c.upper() for c in cmd))     # no password arguments on the command line
        self.assertIn("-development", build_cmd.build_command("U", "P", "m", "1.0.0", 1, "B", True, "l"))

    def test_missing_signing_reports_names_only(self):
        self.assertEqual(build_cmd.missing_signing({}), list(build_cmd.SIGNING_VARS))
        self.assertEqual(build_cmd.missing_signing({v: "x" for v in build_cmd.SIGNING_VARS}), [])


if __name__ == "__main__":
    unittest.main()
