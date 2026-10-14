import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import skill_lint  # noqa: E402
import skill_index  # noqa: E402

GOOD_DESC = "Use when building a widget popup for a mobile game screen."


def make_skill(root, folder, name=None, desc=GOOD_DESC, body="# Body\n", extra_files=None):
    d = os.path.join(root, folder)
    os.makedirs(d, exist_ok=True)
    fm = "---\nname: %s\ndescription: %s\n---\n" % (name if name is not None else folder, desc)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(fm + body)
    for rel, content in (extra_files or {}).items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    return d


def codes(findings, severity=None):
    return [f.code for f in findings if severity is None or f.severity == severity]


class LintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_clean_skill_has_no_errors(self):
        make_skill(self.root, "ui-popup")
        self.assertEqual(codes(skill_lint.lint_dir(self.root), "error"), [])

    def test_unquoted_colon_in_description_is_an_error(self):
        make_skill(self.root, "ui-popup", desc="Popup setup: anchors and roots for a mobile game screen. Use when needed.")
        self.assertIn("yaml-plain-scalar", codes(skill_lint.lint_dir(self.root), "error"))

    def test_quoted_colon_in_description_is_fine(self):
        make_skill(self.root, "ui-popup", desc='"Popup setup: anchors and roots for a mobile game screen. Use when needed."')
        self.assertEqual(codes(skill_lint.lint_dir(self.root), "error"), [])

    def test_name_must_match_folder(self):
        make_skill(self.root, "ui-popup", name="ui-other")
        self.assertIn("name-mismatch", codes(skill_lint.lint_dir(self.root), "error"))

    def test_missing_description(self):
        make_skill(self.root, "ui-popup", desc="")
        self.assertIn("description-length", codes(skill_lint.lint_dir(self.root), "error"))

    def test_description_too_long(self):
        make_skill(self.root, "ui-popup", desc="x" * 301)
        self.assertIn("description-length", codes(skill_lint.lint_dir(self.root), "error"))

    def test_description_too_short(self):
        make_skill(self.root, "ui-popup", desc="short")
        self.assertIn("description-length", codes(skill_lint.lint_dir(self.root), "error"))

    def test_body_too_long(self):
        make_skill(self.root, "ui-popup", body="line\n" * 500)
        self.assertIn("body-too-long", codes(skill_lint.lint_dir(self.root), "error"))

    def test_body_at_limit_is_ok(self):
        make_skill(self.root, "ui-popup", body="line\n" * 450)
        self.assertNotIn("body-too-long", codes(skill_lint.lint_dir(self.root)))

    def test_missing_referenced_file(self):
        make_skill(self.root, "ui-popup", body="See [x](references/missing.md).\n")
        self.assertIn("missing-ref", codes(skill_lint.lint_dir(self.root), "error"))

    def test_existing_referenced_file_ok(self):
        make_skill(self.root, "ui-popup", body="See [x](references/a.md).\n",
                   extra_files={"references/a.md": "hi"})
        self.assertNotIn("missing-ref", codes(skill_lint.lint_dir(self.root)))

    def test_external_and_anchor_links_ignored(self):
        make_skill(self.root, "ui-popup", body="[a](https://x.y) [b](#top) [c](mailto:a@b.c)\n")
        self.assertNotIn("missing-ref", codes(skill_lint.lint_dir(self.root)))

    def test_links_inside_code_fences_ignored(self):
        make_skill(self.root, "ui-popup", body="```\n[x](references/nope.md)\n```\n")
        self.assertNotIn("missing-ref", codes(skill_lint.lint_dir(self.root)))

    def test_duplicate_names(self):
        make_skill(self.root, "ui-a", name="dup")
        make_skill(self.root, "ui-b", name="dup")
        self.assertIn("duplicate-name", codes(skill_lint.lint_dir(self.root), "error"))

    def test_missing_skill_md(self):
        os.makedirs(os.path.join(self.root, "empty-skill"))
        self.assertIn("no-skill-md", codes(skill_lint.lint_dir(self.root), "error"))

    def test_missing_frontmatter(self):
        d = os.path.join(self.root, "ui-popup")
        os.makedirs(d)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("# no frontmatter\n")
        self.assertIn("no-frontmatter", codes(skill_lint.lint_dir(self.root), "error"))

    def test_trigger_collision_is_warning(self):
        shared = "Use when creating or changing any Canvas HUD popup or panel prefab layout"
        make_skill(self.root, "ui-a", desc=shared + " alpha")
        make_skill(self.root, "ui-b", desc=shared + " beta")
        f = skill_lint.lint_dir(self.root)
        self.assertIn("trigger-collision", codes(f, "warn"))
        self.assertNotIn("trigger-collision", codes(f, "error"))

    def test_strict_turns_warnings_into_failure(self):
        shared = "Use when creating or changing any Canvas HUD popup or panel prefab layout"
        make_skill(self.root, "ui-a", desc=shared + " alpha")
        make_skill(self.root, "ui-b", desc=shared + " beta")
        self.assertEqual(skill_lint.main([self.root]), 0)
        self.assertEqual(skill_lint.main(["--strict", self.root]), 1)

    def test_main_exit_code_on_error(self):
        make_skill(self.root, "ui-popup", name="wrong")
        self.assertEqual(skill_lint.main([self.root]), 1)

    def test_quoted_and_folded_description(self):
        d = os.path.join(self.root, "ui-popup")
        os.makedirs(d)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write('---\nname: ui-popup\ndescription: "Use when building a popup: with colon inside it"\n---\nbody\n')
        self.assertEqual(codes(skill_lint.lint_dir(self.root), "error"), [])


class IndexTests(unittest.TestCase):
    def test_index_groups_by_prefix(self):
        with tempfile.TemporaryDirectory() as root:
            make_skill(root, "ui-popup")
            make_skill(root, "ui-list")
            make_skill(root, "econ-gacha")
            text = skill_index.build_index(root)
            self.assertIn("## ui", text)
            self.assertIn("## econ", text)
            self.assertIn("- ui-popup - " + GOOD_DESC, text)
            self.assertLess(text.index("## econ"), text.index("## ui"))


if __name__ == "__main__":
    unittest.main()
