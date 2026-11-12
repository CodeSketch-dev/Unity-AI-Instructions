import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skillkit"))

import skill_paths as sp  # noqa: E402


def make(skills):
    root = Path(tempfile.mkdtemp())
    for rel in skills:
        d = root / rel
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: x\n---\n")
    return root


class SkillPathsTests(unittest.TestCase):
    def test_finds_grouped_skills(self):
        root = make(["ui/ui-always", "gameplay/kcc-x"])
        self.assertEqual([n for n, _ in sp.iter_skills(root)], ["kcc-x", "ui-always"])

    def test_finds_flat_legacy_skills_too(self):
        root = make(["old-flat", "ui/ui-always"])
        self.assertEqual(sorted(n for n, _ in sp.iter_skills(root)), ["old-flat", "ui-always"])

    def test_ignores_groups_without_skill_md_and_non_skill_files(self):
        root = make(["ui/ui-always"])
        (root / "ui" / "notes").mkdir()
        (root / "INDEX.md").write_text("x")
        self.assertEqual([n for n, _ in sp.iter_skills(root)], ["ui-always"])

    def test_skill_dir_resolves_by_name_and_group_is_reported(self):
        root = make(["ui/ui-always"])
        self.assertEqual(Path(sp.skill_dir(root, "ui-always")), root / "ui" / "ui-always")
        self.assertIsNone(sp.skill_dir(root, "nope"))
        self.assertEqual(sp.group_of(root, "ui-always"), "ui")

    def test_orphans_lists_dirs_without_skill_md(self):
        root = make(["ui/ui-always", "lonely"])
        (root / "ui" / "notes").mkdir()
        (root / "lonely" / "SKILL.md").unlink()
        self.assertEqual(sp.orphans(root), ["lonely", "ui/notes"])

    def test_duplicate_names_in_two_groups_are_reported(self):
        root = make(["ui/dup", "gameplay/dup"])
        self.assertEqual(sp.duplicates(root), ["dup"])


if __name__ == "__main__":
    unittest.main()
