import json
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
import gen_task_graph as gt  # noqa: E402
import orchestrator as orch  # noqa: E402


def graph(day_h=16, cut=True):
    return gt.generate(gl.load_gdd(EXAMPLE), day_h, cut)


class GraphTests(unittest.TestCase):
    def test_example_fits_the_day(self):
        g = graph()
        self.assertGreater(len(g["tasks"]), 25)
        self.assertLess(g["totals"]["wall_h"], 16)
        self.assertEqual(g["dropped"], [])

    def test_acyclic_and_dependencies_exist(self):
        g = graph()
        ids = {t["id"] for t in g["tasks"]}
        by = {t["id"]: t for t in g["tasks"]}
        for t in g["tasks"]:
            for d in t["depends_on"]:
                self.assertIn(d, ids)
                self.assertLessEqual(by[d]["phase"], t["phase"], "%s depends on a later phase task %s" % (t["id"], d))
        depth = gt._depths(g["tasks"])      # raises RecursionError on a cycle
        self.assertEqual(len(depth), len(ids))

    def test_every_task_has_skills_verify_and_agent(self):
        for t in graph()["tasks"]:
            self.assertTrue(t["skills"] and t["verify"] and t["agent"] in "PDBUT", t["id"])

    def test_every_listed_skill_exists(self):
        names = set(os.listdir(SK))
        missing = sorted({s for t in graph()["tasks"] for s in t["skills"] if s not in names})
        self.assertEqual(missing, [], missing)

    def test_groups_have_no_claim_conflicts_or_two_editor_tasks(self):
        g = graph()
        groups = {}
        for t in g["tasks"]:
            groups.setdefault(t["group"], []).append(t)
        for name, members in groups.items():
            claims = [c for m in members for c in m["claims"]]
            self.assertEqual(len(claims), len(set(claims)), name)
            self.assertLessEqual(sum(m["agent"] in "BU" for m in members), 1, name)

    def test_ui_screens_become_tasks(self):
        titles = " ".join(t["title"] for t in graph()["tasks"])
        for ui in ("UI-00-hud", "UI-10-skin-shop", "UI-11-revive", "UI-12-settings"):
            self.assertIn(ui, titles)

    def test_scope_cut_drops_p2_then_p1_and_keeps_p0(self):
        g = graph(day_h=7)
        self.assertTrue(g["dropped"])
        self.assertTrue(all(t["priority"] == "P0" or t["system"] == "pipeline" for t in g["tasks"]))
        ids = {t["id"] for t in g["tasks"]}
        for t in g["tasks"]:
            self.assertTrue(set(t["depends_on"]) <= ids)

    def test_world_zones_become_tasks(self):
        zone_tasks = [t for t in graph()["tasks"] if t["key"].startswith("zone-")]
        self.assertEqual(len(zone_tasks), 3)
        self.assertEqual(sorted(t["phase"] for t in zone_tasks), [2, 4, 4])

    def test_markdown_table(self):
        text = gt.to_markdown(graph())
        self.assertIn("| T01 |", text)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.state = orch.init(EXAMPLE, self.d, 16.0)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_init_and_persistence(self):
        s = orch.load(self.d)
        self.assertEqual(s["game"], "Sky Climb")
        self.assertEqual(s["phase"], 0)
        self.assertTrue(os.path.isfile(os.path.join(self.d, "docs", "orchestrator", "log.md")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "docs", "orchestrator", "state.json.tmp")))

    def test_next_respects_dependencies_and_lanes(self):
        first = orch.ready(orch.load(self.d))
        self.assertEqual([t["id"] for t in first], ["T01"])
        orch.mark(self.d, "T01", "in_progress")
        orch.mark(self.d, "T01", "done", evidence=["lint 0 BLOCK"])
        nxt = orch.ready(orch.load(self.d))
        self.assertTrue(nxt)
        self.assertLessEqual(sum(t["agent"] in "BU" for t in nxt), 1)
        self.assertLessEqual(sum(t["agent"] in "PDT" for t in nxt), 4)

    def test_done_needs_evidence_and_deps(self):
        with self.assertRaises(ValueError):
            orch.mark(self.d, "T01", "done")
        with self.assertRaises(ValueError):
            orch.mark(self.d, "T04", "in_progress")        # depends on T02
        with self.assertRaises(KeyError):
            orch.mark(self.d, "T99", "done", evidence=["x"])

    def test_failed_retries_then_blocks(self):
        orch.mark(self.d, "T01", "in_progress")
        orch.mark(self.d, "T01", "failed", note="try 1")
        self.assertEqual(orch.load(self.d)["tasks"]["T01"]["status"], "pending")
        orch.mark(self.d, "T01", "failed")
        orch.mark(self.d, "T01", "failed")
        t = orch.load(self.d)["tasks"]["T01"]
        self.assertEqual((t["status"], t["attempts"]), ("blocked", 3))

    def test_gates_and_phase_advance(self):
        for tid in [t for t in orch.load(self.d)["tasks"] if orch.load(self.d)["tasks"][t]["phase"] == 0]:
            orch.mark(self.d, tid, "done", evidence=["ok"]) if orch.load(self.d)["tasks"][tid]["depends_on"] == [] or True else None
        s = orch.load(self.d)
        self.assertEqual(s["gate"]["G0"], "pass")
        self.assertEqual(s["phase"], 1)

    def test_resume_reconciles_dead_agents_and_missing_evidence(self):
        orch.mark(self.d, "T01", "in_progress", agent="dev-1")
        s, changes = orch.resume(self.d, live={"dev-2"})
        self.assertTrue(any("T01" in c for c in changes))
        self.assertEqual(s["tasks"]["T01"]["status"], "pending")
        orch.mark(self.d, "T01", "in_progress", agent="dev-1")
        s, changes = orch.resume(self.d, live={"dev-1"})
        self.assertEqual(changes, [])
        raw = orch.load(self.d)
        raw["tasks"]["T01"]["status"] = "done"
        raw["tasks"]["T01"].pop("evidence", None)
        orch.save(self.d, raw)
        s, changes = orch.resume(self.d)
        self.assertTrue(any("without evidence" in c for c in changes))

    def test_status_summary(self):
        s = orch.status(orch.load(self.d))
        self.assertEqual(s["counts"]["pending"], len(orch.load(self.d)["tasks"]))
        self.assertEqual(s["done_h"], 0)


class CliTests(unittest.TestCase):
    def test_cli_flow(self):
        d = tempfile.mkdtemp()
        try:
            self.assertEqual(orch.main(["init", EXAMPLE, "--project", d]), 0)
            self.assertEqual(orch.main(["status", "--project", d]), 0)
            self.assertEqual(orch.main(["next", "--project", d]), 0)
            self.assertEqual(orch.main(["mark", "T01", "in_progress", "--project", d]), 0)
            self.assertEqual(orch.main(["mark", "T01", "done", "--project", d]), 1)       # no evidence
            self.assertEqual(orch.main(["mark", "T01", "done", "--project", d, "--evidence", "lint 0 BLOCK"]), 0)
            self.assertEqual(orch.main(["resume", "--project", d]), 0)
            self.assertEqual(orch.main(["bogus"]), 2)
        finally:
            shutil.rmtree(d)

    def test_graph_cli_writes_files(self):
        d = tempfile.mkdtemp()
        try:
            out = os.path.join(d, "tg.json")
            self.assertEqual(gt.main([EXAMPLE, "--out", out]), 0)
            self.assertTrue(json.load(open(out, encoding="utf-8"))["tasks"])
            self.assertTrue(os.path.isfile(os.path.join(d, "tg.md")))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
