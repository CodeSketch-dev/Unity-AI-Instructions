import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from harness import verify  # noqa: E402

PY = sys.executable


def v(name, code, timeout=30):
    return {"name": name, "cmd": [PY, "-c", code], "timeout": timeout}


class VerifyTests(unittest.TestCase):
    def test_all_pass(self):
        ok, res = verify.run_verifiers([v("a", "print('hi')"), v("b", "pass")], tempfile.mkdtemp())
        self.assertTrue(ok)
        self.assertEqual([r["exit"] for r in res], [0, 0])

    def test_stops_at_first_failure_and_keeps_a_tail(self):
        ok, res = verify.run_verifiers([v("a", "import sys; print('boom: 42'); sys.exit(3)"), v("b", "pass")], tempfile.mkdtemp())
        self.assertFalse(ok)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["exit"], 3)
        self.assertIn("boom", res[0]["tail"])

    def test_timeout_is_recorded_and_returns_quickly(self):
        t0 = time.time()
        ok, res = verify.run_verifiers([v("slow", "import time; time.sleep(60)", timeout=1)], tempfile.mkdtemp())
        self.assertFalse(ok)
        self.assertTrue(res[0]["timeout"])
        self.assertLess(time.time() - t0, 20)

    def test_missing_command_is_a_failure_not_a_crash(self):
        ok, res = verify.run_verifiers([{"name": "x", "cmd": ["definitely-not-a-real-binary-xyz"]}], tempfile.mkdtemp())
        self.assertFalse(ok)
        self.assertIn("not found", res[0]["tail"].lower())

    def test_signature_ignores_numbers_and_paths(self):
        bs = chr(92)
        a = {"name": "t", "tail": "AssertionError: 10244 not less than 8000 in C:" + bs + "x" + bs + "y" + bs + "file.py line 12"}
        b = {"name": "t", "tail": "AssertionError: 99 not less than 7 in D:/other/dir/file.py line 400"}
        c = {"name": "t", "tail": "ValueError: totally different"}
        self.assertEqual(verify.signature(a), verify.signature(b))
        self.assertNotEqual(verify.signature(a), verify.signature(c))


if __name__ == "__main__":
    unittest.main()
