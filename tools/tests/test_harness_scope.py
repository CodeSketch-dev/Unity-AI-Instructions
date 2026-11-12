import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from harness import scope  # noqa: E402


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)


def make_repo():
    repo = Path(tempfile.mkdtemp())
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "docs").mkdir()
    (repo / "docs" / "a.md").write_text("a")
    (repo / "src.txt").write_text("s")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo


def violations(repo, before, owns):
    after = scope.snapshot(repo)
    return scope.check_scope(scope.changed_since(before, after), owns, scope.DEFAULT_FORBIDDEN)


class ScopeTests(unittest.TestCase):
    def test_change_inside_owns_passes(self):
        repo = make_repo()
        before = scope.snapshot(repo)
        (repo / "docs" / "new.md").write_text("n")
        self.assertEqual(violations(repo, before, ["docs/**"]), [])

    def test_change_outside_owns_is_flagged(self):
        repo = make_repo()
        before = scope.snapshot(repo)
        (repo / "src.txt").write_text("changed")
        v = violations(repo, before, ["docs/**"])
        self.assertEqual(len(v), 1)
        self.assertIn("src.txt", v[0])

    def test_pre_existing_dirty_file_unchanged_is_ignored(self):
        repo = make_repo()
        (repo / "src.txt").write_text("dirty before the run")
        before = scope.snapshot(repo)
        (repo / "docs" / "new.md").write_text("n")
        self.assertEqual(violations(repo, before, ["docs/**"]), [])

    def test_pre_existing_dirty_file_modified_further_is_flagged(self):
        repo = make_repo()
        (repo / "src.txt").write_text("dirty before the run")
        before = scope.snapshot(repo)
        (repo / "src.txt").write_text("agent touched it")
        self.assertTrue(any("src.txt" in m for m in violations(repo, before, ["docs/**"])))

    def test_forbidden_path_is_flagged_even_inside_owns(self):
        repo = make_repo()
        before = scope.snapshot(repo)
        (repo / ".claude").mkdir()
        (repo / ".claude" / "settings.json").write_text("{}")
        v = violations(repo, before, ["**"])
        self.assertTrue(any("forbidden" in m and "settings.json" in m for m in v), v)

    def test_agent_commit_is_flagged(self):
        repo = make_repo()
        before = scope.snapshot(repo)
        (repo / "docs" / "new.md").write_text("n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "agent commit")
        v = violations(repo, before, ["docs/**"])
        self.assertTrue(any("commit" in m for m in v), v)

    def test_glob_semantics(self):
        self.assertTrue(scope.matches("docs/a/b.md", "docs/**"))
        self.assertTrue(scope.matches("docs/a.md", "docs/*.md"))
        self.assertFalse(scope.matches("docs/a/b.md", "docs/*.md"))


if __name__ == "__main__":
    unittest.main()
