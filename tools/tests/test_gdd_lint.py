import copy
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills")
sys.path.insert(0, os.path.join(SK, "game-orchestrator", "scripts"))
EXAMPLE = os.path.join(SK, "gdd-schema", "assets", "example-sky-climb", "gdd")

import gdd_lint as gl  # noqa: E402


def rules(findings, sev=None):
    return sorted({f.rule for f in findings if sev is None or f.sev == sev})


def fresh():
    d = tempfile.mkdtemp()
    dest = os.path.join(d, "gdd")
    shutil.copytree(EXAMPLE, dest)
    return d, dest


def edit(path, old, new):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    assert old in s, old
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.replace(old, new, 1))


class ExampleTests(unittest.TestCase):
    def test_example_has_no_block(self):
        g = gl.load_gdd(EXAMPLE)
        g["no_fs"] = True
        f = gl.lint(g)
        self.assertEqual([x for x in f if x.sev == "BLOCK"], [], [x for x in f if x.sev == "BLOCK"])

    def test_hash_is_stable_and_changes(self):
        d, g = fresh()
        try:
            a = gl.gdd_hash(g)
            self.assertEqual(a, gl.gdd_hash(g))
            edit(os.path.join(g, "glossary.md"), "Floor", "Level")
            self.assertNotEqual(a, gl.gdd_hash(g))
        finally:
            shutil.rmtree(d)


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.d, self.g = fresh()

    def tearDown(self):
        shutil.rmtree(self.d)

    def lint(self, **kw):
        g = gl.load_gdd(self.g)
        g["no_fs"] = True
        return gl.lint(g, **kw)

    def test_l001_unknown_type_and_missing_key(self):
        edit(os.path.join(self.g, "systems", "S-02-camera.md"), "type: camera", "type: spaceship")
        edit(os.path.join(self.g, "systems", "S-03-input.md"), "title: Touch input\n", "")
        f = self.lint()
        self.assertIn("L001", rules(f, "BLOCK"))
        self.assertGreaterEqual(len([x for x in f if x.rule == "L001"]), 2)

    def test_l002_duplicate_id_broken_dep_cycle(self):
        edit(os.path.join(self.g, "systems", "S-02-camera.md"), "id: S-02-camera", "id: S-01-character")
        edit(os.path.join(self.g, "systems", "S-03-input.md"), "recipe: mobile-input-controls", "recipe: mobile-input-controls\ndepends_on: [S-99-nope]")
        f = [x for x in self.lint() if x.rule == "L002"]
        self.assertTrue(any("duplicate id" in x.message for x in f))
        self.assertTrue(any("S-99-nope" in x.message for x in f))

    def test_l002_cycle(self):
        edit(os.path.join(self.g, "systems", "S-03-input.md"), "recipe: mobile-input-controls", "recipe: mobile-input-controls\ndepends_on: [S-01-character]")
        self.assertTrue(any("cycle" in x.message for x in self.lint() if x.rule == "L002"))

    def test_l003_p0_without_evidence_blocks_p1_warns(self):
        edit(os.path.join(self.g, "systems", "S-01-character.md"), "evidence: [CAP-003@00:12]\n", "evidence: []\n")
        edit(os.path.join(self.g, "systems", "S-01-character.md"), "    evidence: [CAP-005@00:20]\n", "")
        f = self.lint()
        self.assertIn("L003", rules(f, "BLOCK"))
        edit(os.path.join(self.g, "systems", "S-08-monetization.md"), "evidence: [CAP-014@00:10]", "evidence: []")
        self.assertIn("L003", rules(self.lint(), "WARN"))

    def test_l003_unknown_capture_token(self):
        edit(os.path.join(self.g, "systems", "S-02-camera.md"), "CAP-003@00:30", "CAP-777@00:30")
        self.assertTrue(any("CAP-777" in x.message for x in self.lint() if x.sev == "BLOCK"))

    def test_l004_acceptance_needs_tag_and_p0_play_or_edit(self):
        edit(os.path.join(self.g, "systems", "S-02-camera.md"), '"[play] dragging the right half orbits the camera without moving the character"', '"[shot] looks right"')
        self.assertTrue(any(x.rule == "L004" and "[play] or [edit]" in x.message for x in self.lint()))
        edit(os.path.join(self.g, "systems", "S-03-input.md"), '"[play] joystick moves the character and jump is one jump per press"', '"works"')
        edit(os.path.join(self.g, "systems", "S-03-input.md"), '      - "[shot] HUD controls do not overlap at 3 aspect ratios"\n', "")
        self.assertTrue(any(x.rule == "L004" and "verifier tag" in x.message for x in self.lint()))

    def test_l005_unknown_values(self):
        edit(os.path.join(self.g, "systems", "S-01-character.md"), "speed_mps: 4.5", "speed_mps: ?")
        self.assertIn("L005", rules(self.lint(), "BLOCK"))
        edit(os.path.join(self.g, "systems", "S-10-audio.md"), "source: free-pack", "source: ?")
        self.assertIn("L005", rules(self.lint(), "WARN"))

    def test_l006_currency_without_source_or_sink(self):
        edit(os.path.join(self.g, "systems", "S-06-economy.md"), "sinks: [skin_shop]}", "sinks: []}")
        self.assertIn("L006", rules(self.lint(), "BLOCK"))

    def test_l007_unknown_currency_and_slow_first_purchase(self):
        edit(os.path.join(self.g, "economy", "prices.csv"), "skin_02,Ninja,skin,coins", "skin_02,Ninja,skin,rubies")
        self.assertIn("L007", rules(self.lint(), "BLOCK"))
        shutil.rmtree(self.d)
        self.d, self.g = fresh()
        edit(os.path.join(self.g, "systems", "S-06-economy.md"), "income_per_s: 1.2", "income_per_s: 0.01")
        self.assertIn("L007", rules(self.lint(), "WARN"))

    def test_l008_overlap_missing_zone_bad_anchor(self):
        p = os.path.join(self.g, "ui", "UI-00-hud.md")
        edit(p, "size: [200, 200], zone: bottom-right", "size: [2000, 200], zone: bottom-right")
        self.assertTrue(any("overlaps" in x.message for x in self.lint() if x.rule == "L008"))
        edit(p, "zone: top-center, ", "")
        edit(p, "anchor: mid-right", "anchor: nowhere")
        msgs = [x.message for x in self.lint() if x.rule == "L008"]
        self.assertTrue(any("without zone" in m for m in msgs))
        self.assertTrue(any("anchor" in m for m in msgs))

    def test_l009_missing_asset_and_buy(self):
        edit(os.path.join(self.g, "systems", "S-06-economy.md"), "icon: A-022", "icon: A-099")
        self.assertTrue(any("A-099" in x.message for x in self.lint() if x.rule == "L009"))
        edit(os.path.join(self.g, "assets", "assets.csv"), "A-022,icon,gem_icon,own", "A-022,icon,gem_icon,buy")
        self.assertTrue(any("unresolved" in x.message for x in self.lint() if x.rule == "L009"))

    def test_l010_orphan_screen_and_missing_ui_ref(self):
        edit(os.path.join(self.g, "ui", "UI-11-revive.md"), "opened_by: [event:character_dead]\n", "")
        self.assertIn("L010", rules(self.lint(), "WARN"))
        edit(os.path.join(self.g, "systems", "S-07-skin-shop.md"), "ui: UI-10-skin-shop", "ui: UI-77-nope")
        self.assertIn("L010", rules(self.lint(), "BLOCK"))

    def test_l011_budget(self):
        self.assertIn("L011", rules(self.lint(estimate_h=20, day_h=16), "BLOCK"))
        self.assertIn("L011", rules(self.lint(estimate_h=12, day_h=16), "WARN"))
        self.assertNotIn("L011", rules(self.lint(estimate_h=5, day_h=16)))

    def test_l012_coverage(self):
        os.remove(os.path.join(self.g, "systems", "S-02-camera.md"))
        edit(os.path.join(self.g, "00-index.md"), "S-02-camera, ", "")
        edit(os.path.join(self.g, "00-index.md"), "S-02-camera, ", "")
        self.assertTrue(any("camera" in x.message for x in self.lint() if x.rule == "L012"))

    def test_l012_golden_path(self):
        with open(os.path.join(self.g, "qa", "golden-path.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("# Golden path\n- spawn and jump\n")
        self.assertTrue(any("golden" in x.message for x in self.lint() if x.rule == "L012"))

    def test_l013_monetization(self):
        edit(os.path.join(self.g, "systems", "S-08-monetization.md"), "grants: {gems: 100}", "grants: {}")
        self.assertIn("L013", rules(self.lint(), "BLOCK"))
        edit(os.path.join(self.g, "systems", "S-08-monetization.md"), "consent: {gdpr_flow: true}\n", "")
        self.assertTrue(any(x.rule == "L013" and x.sev == "WARN" for x in self.lint()))

    def test_l014_exact_ui_needs_capture_per_state(self):
        edit(os.path.join(self.g, "ui", "UI-10-skin-shop.md"), "captures: [CAP-010@00:05, CAP-011@00:05, CAP-012@00:05, CAP-013@00:05]", "captures: [CAP-010@00:05]")
        self.assertIn("L014", rules(self.lint(), "BLOCK"))

    def test_l015_stale(self):
        g = gl.load_gdd(self.g)
        g["no_fs"] = True
        self.assertIn("L015", rules(gl.lint(g, last_hash="deadbeef"), "INFO"))
        self.assertNotIn("L015", rules(gl.lint(g, last_hash=gl.gdd_hash(self.g))))


class CliTests(unittest.TestCase):
    def test_cli_writes_reports_and_exit_codes(self):
        d, g = fresh()
        try:
            self.assertEqual(gl.main([g, "--no-fs"]), 0)
            self.assertTrue(os.path.isfile(os.path.join(g, "_generated", "lint-report.md")))
            self.assertTrue(os.path.isfile(os.path.join(g, "_generated", "gdd.json")))
            edit(os.path.join(g, "systems", "S-01-character.md"), "speed_mps: 4.5", "speed_mps: ?")
            self.assertEqual(gl.main([g, "--no-fs"]), 1)
            with open(os.path.join(g, "_generated", "questions.md"), encoding="utf-8") as f:
                self.assertIn("speed_mps", f.read())
        finally:
            shutil.rmtree(d)


TEMPLATE = os.path.join(SK, "gdd-schema", "assets", "gdd-template")


class TemplateTests(unittest.TestCase):
    def test_every_type_has_a_parsing_template(self):
        for t in sorted(gl.TYPES):
            path = os.path.join(TEMPLATE, "systems", t + ".md")
            self.assertTrue(os.path.isfile(path), t)
            with open(path, encoding="utf-8") as f:
                fm, _ = gl.miniyaml.split_front_matter(f.read())
            self.assertEqual(fm["type"], t)
            for key in gl.ENVELOPE:
                self.assertIn(key, fm, t)

    def test_blank_template_is_not_lint_clean(self):
        g = gl.load_gdd(TEMPLATE)
        g["no_fs"] = True
        self.assertTrue([x for x in gl.lint(g) if x.sev == "BLOCK"])


if __name__ == "__main__":
    unittest.main()
