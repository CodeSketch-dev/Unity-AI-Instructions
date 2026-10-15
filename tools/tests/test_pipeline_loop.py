import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
SCRIPTS = os.path.join(ROOT, "skills", "game-orchestrator", "scripts")
EXAMPLE = os.path.join(ROOT, "skills", "gdd-schema", "assets", "example-sky-climb", "gdd")
sys.path.insert(0, SCRIPTS)

import pipeline_loop  # noqa: E402
import orchestrator  # noqa: E402


class PipelineLoopTests(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.project)

    def test_first_iteration_updates_state_and_leaves_unity_inconclusive(self):
        result = pipeline_loop.run_once(EXAMPLE, self.project)
        self.assertEqual(result["status"], "inconclusive")
        state = orchestrator.load(self.project)
        self.assertEqual(state["loop"]["iteration"], 1)
        self.assertEqual(state["loop"]["gates"]["gdd"]["result"], "pass")
        self.assertEqual(state["loop"]["gates"]["unity"]["result"], "inconclusive")
        self.assertTrue(state["loop"]["history"])
        self.assertEqual(state["tasks"]["T01"]["status"], "done")
        manifest = os.path.join(self.project, "docs", "orchestrator", "active-skills.json")
        self.assertTrue(os.path.isfile(manifest))
        with open(manifest, encoding="utf-8") as stream:
            self.assertEqual(json.load(stream)["phase"], "phase-0")

    def test_repeated_failure_creates_bounded_repair_and_blocks(self):
        bad = os.path.join(self.project, "gdd")
        shutil.copytree(EXAMPLE, bad)
        with open(os.path.join(bad, "00-index.md"), "w", encoding="utf-8") as f:
            f.write("---\ngame: Broken\n---\n")
        for _ in range(3):
            result = pipeline_loop.run_once(bad, self.project)
        state = orchestrator.load(self.project)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(state["loop"]["repair_queue"][0]["attempts"], 3)
        self.assertTrue(state["loop"]["repair_queue"][0]["blocked"])
        self.assertEqual(state["tasks"]["T01"]["status"], "blocked")

    def test_max_iterations_is_enforced(self):
        first = pipeline_loop.run_once(EXAMPLE, self.project, max_iterations=1)
        second = pipeline_loop.run_once(EXAMPLE, self.project, max_iterations=1)
        self.assertEqual(first["status"], "inconclusive")
        self.assertEqual(second["status"], "stopped")
        self.assertEqual(orchestrator.load(self.project)["loop"]["iteration"], 1)

    def test_cli_result_is_json_serializable(self):
        result = pipeline_loop.run_once(EXAMPLE, self.project)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
