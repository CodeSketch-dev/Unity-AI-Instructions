import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "..", "..", "skills")
for p in ("qa-static-checks", "qa-batch-and-fallbacks", "qa-playmode-smoke"):
    sys.path.insert(0, os.path.join(SK, p, "scripts"))

import qa_asmdef  # noqa: E402
import qa_banned_api  # noqa: E402
import qa_lint_layout  # noqa: E402
import qa_perf_compare  # noqa: E402
import qa_run  # noqa: E402
import qa_scan_refs  # noqa: E402
import qa_unity_batch  # noqa: E402

GUID_A = "a" * 32
GUID_B = "b" * 32


class Proj(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def w(self, rel, text):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return p

    def meta(self, rel, guid):
        self.w(rel + ".meta", "fileFormatVersion: 2\nguid: %s\n" % guid)


class RefTests(Proj):
    PREFAB = ("%%YAML 1.1\n--- !u!1 &100\nGameObject:\n  m_Name: A\n--- !u!114 &200\nMonoBehaviour:\n"
              "  m_Script: {fileID: 11500000, guid: %s, type: 3}\n  _button: {fileID: 0}\n  _target: {fileID: 100}\n  _sprite: {fileID: 21300000, guid: %s, type: 3}\n")

    def test_clean_prefab_passes(self):
        self.meta("Assets/S/A.cs", GUID_A)
        self.meta("Assets/T/s.png", GUID_B)
        self.w("Assets/P/A.prefab", self.PREFAB % (GUID_A, GUID_B))
        f, _ = qa_scan_refs.scan(self.d)
        self.assertEqual(f, [])

    def test_missing_script_and_ref_and_dangling(self):
        self.w("Assets/P/A.prefab", (self.PREFAB % (GUID_A, GUID_B)).replace("_target: {fileID: 100}", "_target: {fileID: 999}"))
        rules = {x["rule"] for x in qa_scan_refs.scan(self.d)[0]}
        self.assertEqual(rules, {"MISSING-SCRIPT", "MISSING-REF", "DANGLING-LOCAL"})

    def test_required_null_field(self):
        self.meta("Assets/S/A.cs", GUID_A)
        self.meta("Assets/T/s.png", GUID_B)
        self.w("Assets/P/A.prefab", self.PREFAB % (GUID_A, GUID_B))
        f, _ = qa_scan_refs.scan(self.d, None, ["^_button$"])
        self.assertEqual([x["rule"] for x in f], ["NULL-REQUIRED"])

    def test_builtin_guid_and_binary_skipped(self):
        self.w("Assets/P/B.prefab", "%YAML 1.1\n--- !u!1 &1\nX:\n  m: {fileID: 10202, guid: 0000000000000000e000000000000000, type: 0}\n")
        self.w("Assets/P/C.unity", "binary\x00data")
        f, binary = qa_scan_refs.scan(self.d)
        self.assertEqual((f, binary), ([], 1))

    def test_full_scan_only_checks_first_party_assets_when_present(self):
        self.w("Assets/_Game/Prefabs/Owned.prefab", "%YAML 1.1\n--- !u!1 &1\nGameObject:\n  m_Name: Owned\n")
        self.w("Assets/Vendor/Broken.prefab", "%YAML 1.1\n--- !u!114 &1\nMonoBehaviour:\n  m_Script: {fileID: 11500000, guid: " + GUID_A + ", type: 3}\n")
        findings, _ = qa_scan_refs.scan(self.d)
        self.assertEqual(findings, [])


class BannedTests(unittest.TestCase):
    def rules(self, code, path="Assets/_Game/Scripts/Logic/A.cs"):
        return [(f["rule"], f["severity"]) for f in qa_banned_api.scan_text(code, path, qa_banned_api.DEFAULT_RULES)]

    def test_hot_versus_cold(self):
        code = "class A {\n void Awake(){ var c = GetComponent<B>(); }\n void Update(){ var c = GetComponent<B>(); }\n}"
        self.assertEqual(self.rules(code), [("GET-COMPONENT-HOT", "error")])

    def test_brace_tracking_leaves_hot_scope(self):
        code = "class A {\n void Update(){ if (x) { y(); } }\n void Start(){ var c = GetComponent<B>(); }\n}"
        self.assertEqual(self.rules(code), [])

    def test_strings_and_comments_ignored(self):
        code = 'class A {\n void Update(){ var s = "GetComponent<B>() {"; // Camera.main\n }\n void Start(){}\n}'
        self.assertEqual(self.rules(code), [])

    def test_allow_comment_needs_reason(self):
        ok = "class A {\n void Update(){ var c = GetComponent<B>(); // qa-allow: GET-COMPONENT-HOT cached lazily once\n }\n}"
        no = "class A {\n void Update(){ var c = GetComponent<B>(); // qa-allow: GET-COMPONENT-HOT\n }\n}"
        self.assertEqual(self.rules(ok), [])
        self.assertEqual(self.rules(no), [("GET-COMPONENT-HOT", "error")])

    def test_playerprefs_and_leftover(self):
        self.assertIn(("PLAYERPREFS", "error"), self.rules("class A { void Start(){ PlayerPrefs.SetInt(\"a\",1); } }"))
        self.assertIn(("LEFTOVER", "error"), self.rules("class A { const float MAX = 203; // REVERT\n}"))

    def test_timescale_allowed_in_debug_paths(self):
        self.assertEqual(self.rules("class A { void Start(){ Time.timeScale = 0; } }", "Assets/_Game/Scripts/Logic/UI/Pause_Popup.cs"), [])
        self.assertIn(("TIMESCALE-SET", "warn"), self.rules("class A { void Start(){ Time.timeScale = 20; } }"))

    def test_expression_bodied_callback_does_not_make_next_method_hot(self):
        code = ("class A {\n void OnTriggerEnterFunc(X t)\n  => t.Go(this);\n"
                " void OnValidate(){ var c = GetComponentInChildren<B>(); }\n}")
        self.assertEqual(self.rules(code), [])

    def test_editor_and_tests_folders_skipped(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "Assets", "_Game", "Scripts", "Editor", "T.cs")
            os.makedirs(os.path.dirname(p))
            open(p, "w").write("class T { void Update(){ PlayerPrefs.DeleteAll(); } }")
            self.assertEqual(qa_banned_api.scan(d), [])
        finally:
            shutil.rmtree(d)


class LayoutTests(unittest.TestCase):
    def test_rules(self):
        good = "namespace Game {\n public class Data_X {\n [SerializeField] int _a;\n const int MAX_N = 1;\n }\n}"
        self.assertEqual(qa_lint_layout.lint_text(good, "Assets/_Game/Scripts/Data/Data_X.cs"), [])
        bad = "namespace Other {\n public class Data_X {\n [SerializeField] int a;\n const int maxN = 1;\n }\n}"
        got = {f["rule"] for f in qa_lint_layout.lint_text(bad, "Assets/_Game/Scripts/Logic/Data_X.cs")}
        self.assertEqual(got, {"NAMESPACE", "ROLE-FOLDER", "SERIALIZE-NAME", "CONST-NAME"})

    def test_no_namespace_and_file_name(self):
        got = {f["rule"] for f in qa_lint_layout.lint_text("public class Foo {}", "Assets/_Game/Scripts/Logic/Bar.cs")}
        self.assertEqual(got, {"NAMESPACE", "FILE-NAME"})


class AsmdefTests(Proj):
    def test_cycle_and_editor_flags(self):
        self.w("Assets/A/A.asmdef", json.dumps({"name": "A", "references": ["B"]}))
        self.w("Assets/B/B.asmdef", json.dumps({"name": "B", "references": ["A"]}))
        self.w("Assets/E/G.Editor.asmdef", json.dumps({"name": "G.Editor", "references": []}))
        rules = {f["rule"] for f in qa_asmdef.scan(self.d)}
        self.assertEqual(rules, {"ASMDEF-CYCLE", "ASMDEF-EDITOR"})

    def test_guid_references_resolve(self):
        self.w("Assets/A/A.asmdef", json.dumps({"name": "A", "references": ["GUID:" + GUID_B]}))
        self.w("Assets/B/B.asmdef", json.dumps({"name": "B", "references": ["A"]}))
        self.meta("Assets/B/B.asmdef", GUID_B)
        self.assertIn("ASMDEF-CYCLE", {f["rule"] for f in qa_asmdef.scan(self.d)})

    def test_editor_leak(self):
        self.w("Assets/_Game/Scripts/L.cs", "using UnityEditor;\nclass L {}")
        self.w("Assets/_Game/Scripts/OK.cs", "#if UNITY_EDITOR\nusing UnityEditor;\n#endif\nclass OK {}")
        self.w("Assets/_Game/Scripts/Editor/E.cs", "using UnityEditor;\nclass E {}")
        got = [f["file"] for f in qa_asmdef.scan(self.d) if f["rule"] == "EDITOR-LEAK"]
        self.assertEqual(got, ["Assets/_Game/Scripts/L.cs"])

    def test_tests_asmdef_needs_constraint(self):
        self.w("Assets/T/T.asmdef", json.dumps({"name": "T.Tests", "references": ["UnityEngine.TestRunner"]}))
        self.assertIn("ASMDEF-TESTS", {f["rule"] for f in qa_asmdef.scan(self.d)})

    def test_editor_assembly_may_use_test_runner_without_being_a_test_assembly(self):
        self.w("Assets/E/Tool.Editor.asmdef", json.dumps({
            "name": "Tool.Editor",
            "references": ["UnityEngine.TestRunner", "UnityEditor.TestRunner"],
            "includePlatforms": ["Editor"],
        }))
        self.assertNotIn("ASMDEF-TESTS", {f["rule"] for f in qa_asmdef.scan(self.d)})


class RunTests(Proj):
    def test_static_records_stage_and_blocks_pass_claims(self):
        self.w("Assets/_Game/Scripts/Logic/A.cs", "namespace Game { class A { void Update(){ Find(); GameObject.Find(\"x\"); } } }")
        self.assertEqual(qa_run.main(["static", "--project", self.d]), 1)
        st = qa_run.load_state(self.d)
        self.assertEqual(st["stages"]["S2"]["result"], "fail")
        self.assertTrue(st["stages"]["S2"]["signature"])

    def test_record_requires_evidence_for_pass(self):
        self.assertEqual(qa_run.record(self.d, "S1", "pass", ""), 1)
        self.assertEqual(qa_run.record(self.d, "S1", "pass", "Console clean after refresh"), 0)

    def test_repeat_signature_escalates(self):
        for _ in range(3):
            qa_run.record(self.d, "S3", "fail", "x", "SIG")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            qa_run.record(self.d, "S3", "fail", "x", "SIG")
        self.assertIn("ESCALATE", buf.getvalue())

    def test_verdicts(self):
        ok = {s: {"result": "pass"} for s in qa_run.STAGES}
        self.assertEqual(qa_run.compute_verdict(ok, "mcp", "1", "fresh")[0], "PASS")
        self.assertEqual(qa_run.compute_verdict(ok, "mcp", "60", "fresh")[0], "INCONCLUSIVE")
        self.assertEqual(qa_run.compute_verdict(ok, "mcp", "1", "unknown")[0], "INCONCLUSIVE")
        only_static = {"S2": {"result": "pass"}}
        self.assertEqual(qa_run.compute_verdict(only_static, "static", "1", "fresh")[0], "STATIC-PASS")
        bad = dict(ok, S4={"result": "fail"})
        self.assertEqual(qa_run.compute_verdict(bad, "mcp", "1", "fresh")[0], "FAIL")
        noted = dict(ok, S5={"result": "pass", "soft_note": "icon ratio, matches reference"})
        self.assertEqual(qa_run.compute_verdict(noted, "mcp", "1", "fresh")[0], "PASS-WITH-NOTES")
        partial = {"S1": {"result": "pass"}, "S2": {"result": "pass"}}
        self.assertEqual(qa_run.compute_verdict(partial, "mcp", "1", "fresh")[0], "INCONCLUSIVE")

    def test_verdict_writes_report_and_exit_code(self):
        qa_run.record(self.d, "S2", "pass", "clean")
        rc = qa_run.main(["verdict", "--project", self.d, "--task", "t", "--rung", "static", "--save", "fresh"])
        self.assertEqual(rc, 1)  # STATIC-PASS is never done
        reports = os.listdir(os.path.join(self.d, "docs", "qa", "reports"))
        self.assertEqual(sorted(x.rsplit(".", 1)[1] for x in reports), ["json", "md"])


class BatchTests(Proj):
    XML = ('<test-run><test-suite><test-case name="A" fullname="N.A" result="Passed"/>'
           '<test-case name="B" fullname="N.B" result="Failed"><failure><message>boom\nmore</message></failure></test-case>'
           '<test-case name="C" fullname="N.C" result="Skipped"/></test-suite></test-run>')

    def test_parse(self):
        p = self.w("r.xml", self.XML)
        self.assertEqual(qa_unity_batch.parse_results(p), (1, 1, 1, ["N.B: boom"]))

    def test_pinned_version_and_command(self):
        self.w("ProjectSettings/ProjectVersion.txt", "m_EditorVersion: 6000.0.78f1\nm_EditorVersionWithRevision: x\n")
        self.assertEqual(qa_unity_batch.pinned_version(self.d), "6000.0.78f1")
        cmd = qa_unity_batch.build_command("U", self.d, "EditMode", "Qa_", "r.xml", "l.log")
        self.assertIn("-runTests", cmd)
        self.assertEqual(cmd[cmd.index("-testFilter") + 1], "Qa_")
        self.assertNotIn("-quit", cmd)

    def test_lockfile_blocks(self):
        self.assertFalse(qa_unity_batch.editor_running(self.d))
        self.w("Temp/UnityLockfile", "")
        self.assertTrue(qa_unity_batch.editor_running(self.d))


class HookTests(Proj):
    def run_hook(self, rel):
        import subprocess
        hook = os.path.join(HERE, "..", "..", "hooks", "scripts", "qa_post_edit.py")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.d)
        ev = json.dumps({"tool_input": {"file_path": os.path.join(self.d, rel)}})
        return subprocess.run([sys.executable, "-I", hook], input=ev, capture_output=True, text=True, env=env, timeout=30)

    def test_blocks_hard_issue_in_edited_cs(self):
        os.makedirs(os.path.join(self.d, "ProjectSettings"))
        self.w("Assets/_Game/Scripts/Logic/A.cs", "namespace Game { class A { void Update(){ GameObject.Find(\"x\"); } } }")
        r = self.run_hook("Assets/_Game/Scripts/Logic/A.cs")
        self.assertEqual(r.returncode, 2)
        self.assertIn("FIND-OBJECT", r.stderr)

    def test_silent_for_clean_file_and_non_unity_project(self):
        self.w("Assets/_Game/Scripts/Logic/B.cs", "namespace Game { class B { void Start(){ } } }")
        self.assertEqual(self.run_hook("Assets/_Game/Scripts/Logic/B.cs").returncode, 0)   # no ProjectSettings: not a Unity project
        os.makedirs(os.path.join(self.d, "ProjectSettings"))
        self.assertEqual(self.run_hook("Assets/_Game/Scripts/Logic/B.cs").returncode, 0)

    def test_blocks_missing_script_in_prefab(self):
        os.makedirs(os.path.join(self.d, "ProjectSettings"))
        self.w("Assets/P/A.prefab", "%YAML 1.1\n--- !u!114 &1\nMonoBehaviour:\n  m_Script: {fileID: 11500000, guid: " + GUID_A + ", type: 3}\n")
        self.assertEqual(self.run_hook("Assets/P/A.prefab").returncode, 2)


class PerfTests(unittest.TestCase):
    def test_regression_rules(self):
        base = {"scenarios": {"home": {"batches": 100, "setpass": 20, "gc_bytes_per_frame": 0, "frame_p95_ms": 10, "memory_mb": 500}}}
        same = {"scenarios": {"home": {"batches": 105, "setpass": 20, "gc_bytes_per_frame": 100, "frame_p95_ms": 11, "memory_mb": 520}}}
        worse = {"scenarios": {"home": {"batches": 130, "setpass": 20, "gc_bytes_per_frame": 900, "frame_p95_ms": 10, "memory_mb": 500}}}
        self.assertFalse(qa_perf_compare.compare(same, base)[1])
        rows, failed = qa_perf_compare.compare(worse, base)
        self.assertTrue(failed)
        self.assertEqual({r[1] for r in rows if r[3] == "FAIL"}, {"batches", "gc_bytes_per_frame"})

    def test_new_scenario_has_no_baseline(self):
        rows, failed = qa_perf_compare.compare({"scenarios": {"x": {"batches": 1}}}, {"scenarios": {}})
        self.assertFalse(failed)
        self.assertEqual(rows[0][3], "NEW")


if __name__ == "__main__":
    unittest.main()
