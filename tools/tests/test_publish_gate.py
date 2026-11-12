import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "publish"))

import publish_gate as pg  # noqa: E402


class PublishGateTests(unittest.TestCase):
    def test_layout_violation_blocks_publish(self):
        root = Path(tempfile.mkdtemp())
        (root / "AGENTS.md").write_text("x")
        (root / "stray.ps1").write_text("x")
        ok, report = pg.check_gate(root, run_tests=False)
        self.assertFalse(ok)
        self.assertIn("stray.ps1", report)

    def test_clean_layout_passes_without_tests(self):
        root = Path(tempfile.mkdtemp())
        (root / "AGENTS.md").write_text("x")
        ok, report = pg.check_gate(root, run_tests=False)
        self.assertTrue(ok, report)

    def test_failing_lint_tests_block_publish(self):
        root = Path(tempfile.mkdtemp())
        (root / "AGENTS.md").write_text("x")
        t = root / "tools" / "lint" / "tests"
        t.mkdir(parents=True)
        (t / "test_bad.py").write_text("def test_x():\n    assert False\n")
        ok, report = pg.check_gate(root, run_tests=True)
        self.assertFalse(ok)
        self.assertIn("lint tests", report)


if __name__ == "__main__":
    unittest.main()


class PytestMissingTests(unittest.TestCase):
    def test_missing_pytest_gives_accurate_message_not_fake_test_failure(self):
        root = Path(tempfile.mkdtemp())
        (root / "AGENTS.md").write_text("x")
        (root / "tools" / "lint" / "tests").mkdir(parents=True)
        pg._pytest_missing = lambda: True
        try:
            ok, report = pg.check_gate(root, run_tests=True)
        finally:
            del pg._pytest_missing
            import importlib
            importlib.reload(pg)
        self.assertFalse(ok)
        self.assertIn("pip install pytest", report)
        self.assertNotIn("lint tests failed", report)
