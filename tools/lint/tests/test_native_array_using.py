import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import engine

RULE_ID = "native-array-using-mutation"
PATH = "Assets/_Game/Scripts/Editor/ArrayTool.cs"

class NativeArrayUsingTests(unittest.TestCase):
    def hits(self, source):
        return [v for v in engine.lint_text(PATH, source) if v.rule_id == RULE_ID]

    def test_bad_fixture_and_exact_skill_path(self):
        source = (HERE / "fixtures/bad_native_array_using.cs").read_text()
        expected = [i for i, line in enumerate(source.splitlines(), 1) if "// bad" in line]
        found = self.hits(source)
        self.assertEqual([v.line for v in found], expected)
        self.assertTrue(all(".claude/skills/native-array-using-mutation/SKILL.md" in v.message for v in found))

    def test_good_fixture(self):
        self.assertEqual(self.hits((HERE / "fixtures/good_native_array_using.cs").read_text()), [])

    def test_opt_out_and_read_only(self):
        source = "void F(){ using var a = new NativeArray<int>(4, Allocator.Temp);\na[0] = 1; // lint-ok:native-array-using-mutation deliberate compile fixture\nRead(a[0]); }"
        self.assertEqual(self.hits(source), [])

    def test_nested_shadow_binding_and_using_statement_lifetime(self):
        source = "void F(){ using var a = new NativeArray<int>(4, Allocator.Temp); { var a = GetOther(); a[0] = 1; } a[0] = 2; }"
        self.assertEqual(len(self.hits(source)), 1)
        source = "void F(){ using (NativeArray<int> a = GetValues()) { Read(a[0]); } var a = GetOther(); a[0] = 1; }"
        self.assertEqual(self.hits(source), [])

    def test_strings_comments_multiline_and_alias(self):
        source = 'void F(){\nvar original = new NativeArray<int>(4, Allocator.Temp);\nusing var a = original;\nvar s = "a[0] = 2;"; /* a[0]++; */\na[\n0\n] *= 2;\n}'
        self.assertEqual([v.line for v in self.hits(source)], [5])
        self.assertEqual(self.hits('void F(){ var s = """ using var a = new NativeArray<int>(); a[0] = 1; """; }'), [])

    def test_callback_lines_dedup_suppression_and_vendor_exclusion(self):
        rule = engine.Rule("callback", r"(?!)", "Fix binding.", "example", exclude_dirs=(), scan=lambda _: [2, 2, 0, 99, 3])
        source = "one\ntwo\nthree // lint-ok:callback reason"
        found = engine.lint_text(PATH, source, [rule])
        self.assertEqual([v.line for v in found], [2])
        self.assertEqual(engine.lint_text("Packages/X/Code.cs", source, [rule]), [])
        self.assertEqual(engine.lint_text("Assets/Logic/Old.cs", "Bad()", [engine.Rule("old", r"Bad\(", "Old unchanged.", "old")])[0].line, 1)

    def test_multiple_typed_bindings_and_single_statement_scope(self):
        source = "void F(){ using NativeArray<int> a = GetA(), b = GetB(); b[0] = 1; }"
        self.assertEqual(len(self.hits(source)), 1)
        source = "void F(){ using (NativeArray<int> a = GetA()) a[0]++; var a = GetOther(); a[0] = 2; }"
        self.assertEqual(len(self.hits(source)), 1)

    def test_qualified_generic_alias_and_no_read_false_positive(self):
        source = "void F(){ using var a = new global::Unity.Collections.NativeArray<Pair<int,float>>(4, Allocator.Temp); if(a[0] == other[0]) Read(a[1]); a[2] >>= 1; }"
        self.assertEqual(len(self.hits(source)), 1)

if __name__ == "__main__":
    unittest.main()
