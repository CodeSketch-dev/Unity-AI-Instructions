import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "publish"))

import repo_layout_lint as rl  # noqa: E402


def make_repo(files=(), dirs=()):
    root = Path(tempfile.mkdtemp())
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    for f in files:
        p = root / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    return root


class LayoutLintTests(unittest.TestCase):
    def test_clean_tree_passes(self):
        root = make_repo(files=["AGENTS.md", "sync.bat", "skills/ui/a/SKILL.md", "hooks/ps1/x.ps1", "data/skill_router.json"])
        self.assertEqual(rl.check_layout(root), [])

    def test_stray_ps1_at_root_is_flagged(self):
        root = make_repo(files=["AGENTS.md", "stray_hook.ps1"])
        msgs = rl.check_layout(root)
        self.assertEqual(len(msgs), 1)
        self.assertIn("stray_hook.ps1", msgs[0])
        self.assertIn("docs/REPO-LAYOUT.md", msgs[0])

    def test_unknown_root_dir_is_flagged(self):
        root = make_repo(files=["AGENTS.md"], dirs=["random_stuff"])
        self.assertTrue(any("random_stuff" in m for m in rl.check_layout(root)))

    def test_json_data_must_live_in_data(self):
        root = make_repo(files=["AGENTS.md", "skill_router.json"])
        msgs = rl.check_layout(root)
        self.assertTrue(any("skill_router.json" in m and "data/" in m for m in msgs))

    def test_skill_folder_without_skill_md_is_flagged(self):
        root = make_repo(files=["AGENTS.md", "skills/broken/notes.txt"])
        self.assertTrue(any("skills/broken" in m for m in rl.check_layout(root)))

    def test_dot_dirs_are_ignored(self):
        root = make_repo(files=["AGENTS.md"], dirs=[".git", ".local", ".publish-backup"])
        self.assertEqual(rl.check_layout(root), [])


class WidthTests(unittest.TestCase):
    def test_folder_with_too_many_entries_is_flagged(self):
        root = make_repo(files=["AGENTS.md"] + ["docs/note%d.md" % i for i in range(rl.MAX_ENTRIES + 1)])
        msgs = rl.check_layout(root)
        self.assertTrue(any("docs/" in m and "entries" in m for m in msgs), msgs)

    def test_exempt_folder_may_be_wide(self):
        root = make_repo(files=["AGENTS.md"] + ["tools/tests/t%d.py" % i for i in range(rl.MAX_ENTRIES + 5)])
        self.assertEqual([m for m in rl.check_layout(root) if "tools/tests" in m], [])

    def test_old_top_level_dirs_are_flagged(self):
        root = make_repo(files=["AGENTS.md"], dirs=["lint", "evals", "templates", "packages"])
        flagged = " ".join(rl.check_layout(root))
        for d in ("lint/", "evals/", "templates/", "packages/"):
            self.assertIn(d, flagged)

    def test_projects_txt_must_live_in_data(self):
        root = make_repo(files=["AGENTS.md", "projects.txt"])
        self.assertTrue(any("projects.txt" in m for m in rl.check_layout(root)))


class GroupedSkillTests(unittest.TestCase):
    def test_flat_skill_is_flagged_with_allowed_groups(self):
        root = make_repo(files=["AGENTS.md", "skills/foo/SKILL.md"])
        msgs = rl.check_layout(root)
        self.assertTrue(any("skills/foo" in m and "skills/<group>/" in m and "ui" in m for m in msgs), msgs)

    def test_unknown_group_is_flagged(self):
        root = make_repo(files=["AGENTS.md", "skills/zzz/foo/SKILL.md"])
        self.assertTrue(any("zzz" in m and "group" in m for m in rl.check_layout(root)))

    def test_valid_grouped_skill_passes(self):
        root = make_repo(files=["AGENTS.md", "skills/gameplay/kcc-x/SKILL.md", "skills/ui/ui-y/SKILL.md"])
        self.assertEqual(rl.check_layout(root), [])

    def test_group_over_limit_is_flagged(self):
        root = make_repo(files=["AGENTS.md"] + ["skills/ui/s%d/SKILL.md" % i for i in range(rl.SKILL_GROUP_MAX + 1)])
        self.assertTrue(any("skills/ui" in m and "entries" in m for m in rl.check_layout(root)))

    def test_same_skill_name_in_two_groups_is_flagged(self):
        root = make_repo(files=["AGENTS.md", "skills/ui/dup/SKILL.md", "skills/gameplay/dup/SKILL.md"])
        self.assertTrue(any("dup" in m and "twice" in m for m in rl.check_layout(root)))


if __name__ == "__main__":
    unittest.main()
