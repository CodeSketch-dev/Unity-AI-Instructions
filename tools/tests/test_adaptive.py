import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from adaptive import classify, loop, metrics, selector, skill_proposals, store, ui_adapter  # noqa: E402

CAT, ENV = "unity.run_tests", "os=windows|app=unity|ver=6"


def add(conn, method, n, ok=True, lat=1000.0, verified=True, env=ENV, cat=CAT, age_days=0.0, tok=None, pred=None, t0=None):
    base = (t0 or time.time()) - age_days * 86400
    for i in range(n):
        store.record_run(conn, cat, env, method, ok, verified, latency_ms=lat, in_tok=tok, out_tok=tok, predicted_p=pred,
                         ts_end=base - (n - i) * 0.001)


class Base(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        os.environ["ADAPTIVE_HOME"] = self.home
        os.environ.pop("ADAPTIVE_STOP", None)
        self.conn = store.connect()

    def tearDown(self):
        self.conn.close()
        os.environ.pop("ADAPTIVE_HOME", None)
        shutil.rmtree(self.home, ignore_errors=True)


class ClassifyTests(unittest.TestCase):
    def test_simple_task_takes_fast_path(self):
        r = classify.classify("find where is PlayerController defined")
        self.assertEqual(r["category"], "code.search")
        self.assertTrue(r["fast_path"])
        self.assertIn(r["complexity"], ("trivial", "simple"))

    def test_complex_critical_task_is_not_fast(self):
        r = classify.classify("delete all old build folders in the whole repository, then deploy to production and publish the result after that "
                              "update every config and then run all tests and finally push")
        self.assertTrue(r["critical"])
        self.assertFalse(r["fast_path"])
        self.assertEqual(r["complexity"], "complex")

    def test_categories_and_needs(self):
        self.assertEqual(classify.classify("fix CS0246 compile error")["category"], "unity.compile_errors")
        r = classify.classify("click the OK button in the Notepad dialog")
        self.assertEqual(r["category"], "windows.form_ui")
        self.assertEqual(r["candidates"][0], "ui_automation_scoped")
        self.assertIn("ui_automation", r["needs"])


class SelectorTests(Base):
    def test_no_data_uses_prior_order(self):
        r = selector.select(self.conn, CAT, ["a", "b"], ENV)
        self.assertEqual((r["method"], r["source"]), ("a", "prior"))

    def test_data_overrides_prior_and_repeated_task_gets_cheaper(self):
        add(self.conn, "a", 8, lat=3000)
        add(self.conn, "b", 8, lat=400)
        r = selector.select(self.conn, CAT, ["a", "b"], ENV, explore=False)
        self.assertEqual((r["method"], r["source"]), ("b", "data"))

    def test_low_success_method_excluded_even_if_fast(self):
        add(self.conn, "fast_flaky", 6, ok=False, lat=100)
        add(self.conn, "fast_flaky", 6, ok=True, lat=100)
        add(self.conn, "slow_solid", 12, lat=5000)
        r = selector.select(self.conn, CAT, ["fast_flaky", "slow_solid"], ENV, profile="speed", explore=False)
        self.assertEqual(r["method"], "slow_solid")

    def test_unverified_success_is_not_counted(self):
        add(self.conn, "a", 10, ok=True, verified=False)
        s = selector.method_stats(store.scope_runs(self.conn, CAT, ENV, "a"))
        self.assertEqual(s["p"], 0.0)
        self.assertGreater(s["unverified_frac"], 0.99)

    def test_few_samples_do_not_conclude(self):
        add(self.conn, "a", 2, lat=100)
        add(self.conn, "b", 2, lat=9000)
        r = selector.select(self.conn, CAT, ["b", "a"], ENV)
        self.assertEqual((r["method"], r["source"]), ("b", "prior"))

    def test_missing_tokens_are_unknown_not_zero(self):
        add(self.conn, "a", 8)
        add(self.conn, "b", 8, lat=500)
        row = self.conn.execute("SELECT in_tok, out_tok FROM runs LIMIT 1").fetchone()
        self.assertEqual((row[0], row[1]), (None, None))
        r = selector.select(self.conn, CAT, ["a", "b"], ENV, profile="tokens", explore=False)
        self.assertIsNone(r["stats"]["a"]["tok"])
        self.assertIn("tokens UNKNOWN", r["reason"])

    def test_known_tokens_used_when_measured(self):
        add(self.conn, "a", 8, lat=500, tok=5000)
        add(self.conn, "b", 8, lat=500, tok=500)
        r = selector.select(self.conn, CAT, ["a", "b"], ENV, profile="tokens", explore=False)
        self.assertEqual(r["method"], "b")

    def test_environment_change_not_reused(self):
        add(self.conn, "a", 10, env="os=windows|app=unity|ver=5")
        r = selector.select(self.conn, CAT, ["b", "a"], "os=windows|app=unity|ver=6")
        self.assertTrue(r["env_changed"]["changed"])
        self.assertEqual(r["source"], "prior")
        self.assertEqual(r["method"], "b")

    def test_other_app_data_not_applied(self):
        add(self.conn, "a", 12, env="os=windows|app=notepad|ver=1")
        r = selector.select(self.conn, CAT, ["b", "a"], "os=windows|app=unity|ver=1")
        self.assertEqual((r["method"], r["source"]), ("b", "prior"))
        self.assertFalse(r["env_changed"]["changed"])

    def test_old_data_loses_weight(self):
        add(self.conn, "a", 10, age_days=240)
        s = selector.method_stats(store.scope_runs(self.conn, CAT, ENV, "a"))
        self.assertLess(s["n_eff"], selector.MIN_N)

    def test_regression_detected_and_demoted(self):
        add(self.conn, "a", 10, lat=500)
        add(self.conn, "a", 5, ok=False, lat=500)
        add(self.conn, "b", 10, lat=900)
        rows = store.scope_runs(self.conn, CAT, ENV, "a")
        self.assertTrue(selector.detect_regression(rows)["regressed"])
        r = selector.select(self.conn, CAT, ["a", "b"], ENV, explore=False)
        self.assertEqual(r["method"], "b")
        self.assertIn("a", r["regression"])

    def test_latency_regression(self):
        add(self.conn, "a", 10, lat=100)
        add(self.conn, "a", 5, lat=400)
        self.assertIn("latency", selector.detect_regression(store.scope_runs(self.conn, CAT, ENV, "a"))["why"])

    def test_exploration_bounded_and_blocked_when_critical(self):
        add(self.conn, "a", 9, lat=3000)  # 9 runs: the next decision is the 10th -> bounded exploration of untested b
        r = selector.select(self.conn, CAT, ["a", "b"], ENV)
        self.assertEqual((r["method"], r["source"]), ("b", "explore"))
        self.assertEqual(r["fallbacks"][0], "a")
        crit = selector.select(self.conn, CAT, ["a", "b"], ENV, critical=True)
        self.assertEqual((crit["method"], crit["source"], crit["profile"]), ("a", "data", "accuracy"))
        add(self.conn, "a", 1, lat=3000)  # 10 runs: not an exploration slot
        self.assertEqual(selector.select(self.conn, CAT, ["a", "b"], ENV)["source"], "data")

    def test_no_exploration_when_best_is_cheap_and_reliable(self):
        add(self.conn, "a", 39, lat=50)  # 39 runs hits the exploration slot, but a is cheap and lb>=0.95
        r = selector.select(self.conn, CAT, ["a", "b"], ENV)
        self.assertEqual((r["method"], r["source"]), ("a", "data"))

    def test_calibration_corrects_overconfidence(self):
        add(self.conn, "a", 10, ok=True, pred=0.95)
        add(self.conn, "a", 10, ok=False, pred=0.95)
        c = selector.calibration(self.conn, CAT, ENV)
        self.assertLess(c["offset"], -0.2)
        self.assertGreater(c["brier"], 0.2)

    def test_reset_hides_history_and_undo_restores(self):
        add(self.conn, "a", 10)
        rid = store.reset(self.conn, CAT, ENV, "a")
        time.sleep(0.01)
        self.assertEqual(len(store.scope_runs(self.conn, CAT, ENV, "a")), 0)
        store.undo_reset(self.conn, rid)
        self.assertEqual(len(store.scope_runs(self.conn, CAT, ENV, "a")), 10)
        self.assertTrue(os.listdir(os.path.join(self.home, "backups")))

    def test_summary_is_aggregate_only(self):
        add(self.conn, "a", 3)
        rows = store.summary(self.conn, CAT)
        self.assertEqual(rows[0]["n"], 3)
        self.assertNotIn("fail_reason", rows[0])

    def test_simulated_repeated_task_total_latency_drops(self):
        """SIMULATION with fixed synthetic latencies (not a real benchmark): proves the learning loop converges."""
        lat = {"slow_prior": 3000.0, "fast": 400.0}
        total_adaptive = total_static = 0.0
        for i in range(40):
            r = selector.select(self.conn, CAT, ["slow_prior", "fast"], ENV, explore=(i % 2 == 0))
            m = r["method"]
            total_adaptive += lat[m]
            total_static += lat["slow_prior"]
            add(self.conn, m, 1, lat=lat[m])
            if m == "slow_prior" and i == 8:
                add(self.conn, "fast", 6, lat=400)  # exploration found it once
        self.assertLess(total_adaptive, total_static)


class StoreTests(Base):
    def test_privacy_redaction(self):
        txt = "failed token=abc123SECRET key sk-ABCDEFGHIJKLMNOP1234 user a.b@example.com at C:\\Users\\Code Sketch\\proj Bearer abcdefgh12345678 " + "x" * 60
        red = store.redact(txt)
        for bad in ("abc123SECRET", "sk-ABCDEF", "a.b@example.com", "Code Sketch", "abcdefgh12345678", "x" * 40):
            self.assertNotIn(bad, red)
        store.record_run(self.conn, "c", "e", "m", False, fail_reason=txt)
        self.assertNotIn("example.com", self.conn.execute("SELECT fail_reason FROM runs").fetchone()[0])
        self.assertEqual(store.clean_key("Bad Key; DROP TABLE"), "bad_key__drop_table")

    def test_negative_or_garbage_numbers_become_unknown(self):
        store.record_run(self.conn, "c", "e", "m", True, True, latency_ms=-5, in_tok="abc")
        row = self.conn.execute("SELECT latency_ms, in_tok FROM runs").fetchone()
        self.assertEqual((row[0], row[1]), (None, None))

    def test_migration_v1_to_v2_keeps_data_and_backs_up(self):
        path = os.path.join(self.home, "old.db")
        c = sqlite3.connect(path)
        store.apply_upto(c, 1)
        c.execute("INSERT INTO runs(ts_end,category,env,method,success,verified,latency_ms) VALUES(1.0,'c','e','m',1,1,10)")
        c.commit()
        c.close()
        c2 = store.connect(path)
        self.assertEqual(store._version(c2), store.SCHEMA_VERSION)
        self.assertEqual(c2.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 1)
        self.assertIn("task_fp", [r[1] for r in c2.execute("PRAGMA table_info(runs)")])
        self.assertTrue([f for f in os.listdir(os.path.join(self.home, "backups")) if "premigrate-v1" in f])
        c2.close()

    def test_newer_schema_refused(self):
        path = os.path.join(self.home, "new.db")
        c = store.connect(path)
        c.execute("UPDATE meta SET v='99' WHERE k='schema_version'")
        c.commit()
        c.close()
        with self.assertRaises(RuntimeError):
            store.connect(path)

    def test_prune_caps_rows(self):
        add(self.conn, "a", 30)
        store.prune(self.conn, max_rows=20, keep_rows=10)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 10)

    def test_backup_and_restore(self):
        add(self.conn, "a", 3)
        b = store.backup(None, "t")
        add(self.conn, "a", 2)
        self.conn.close()
        store.restore(None, b)
        self.conn = store.connect()
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 3)


class LoopTests(Base):
    def test_failure_recovers_with_fallback_and_records(self):
        calls = {"a": 0}

        def a(ctx):
            calls["a"] += 1
            raise RuntimeError("boom")
        res = loop.run([loop.Step("a", a, verify=lambda r, c: True), loop.Step("b", lambda c: 7, verify=lambda r, c: r == 7)],
                       CAT, ENV, conn=self.conn)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["method"], "b")
        self.assertEqual(calls["a"], 2)  # one safe retry of the idempotent step, then fallback
        last = res["attempts"][-1]
        self.assertGreaterEqual(last["retries"], 1)
        self.assertIsNotNone(last["recovery_ms"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 3)

    def test_non_idempotent_never_retried(self):
        calls = {"n": 0}

        def pay(ctx):
            calls["n"] += 1
            raise RuntimeError("network")
        res = loop.run([loop.Step("pay", pay, idempotent=False), loop.Step("alt", lambda c: 1, verify=lambda r, c: True)], CAT, ENV)
        self.assertEqual(res["status"], "needs_manual_check")
        self.assertEqual(calls["n"], 1)

    def test_non_idempotent_falls_back_only_when_proven_untouched(self):
        res = loop.run([loop.Step("w", lambda c: 1 / 0, idempotent=False, state_check=lambda: "not_applied"),
                        loop.Step("alt", lambda c: 1, verify=lambda r, c: True)], CAT, ENV)
        self.assertEqual((res["status"], res["method"]), ("ok", "alt"))

    def test_timeout_is_a_failure(self):
        res = loop.run([loop.Step("slow", lambda c: time.sleep(0.5), verify=lambda r, c: True, timeout_s=0.05)], CAT, ENV,
                       max_retries_same=0)
        self.assertEqual(res["status"], "failed")
        self.assertIn("timeout", res["attempts"][0]["fail_reason"])

    def test_no_verification_stops_and_is_not_learned_as_success(self):
        res = loop.run([loop.Step("a", lambda c: 1)], CAT, ENV, conn=self.conn)
        self.assertEqual(res["status"], "no_verification")
        row = self.conn.execute("SELECT success, verified FROM runs").fetchone()
        self.assertEqual((row[0], row[1]), (0, 0))

    def test_allow_unverified_records_verified_zero(self):
        res = loop.run([loop.Step("a", lambda c: 1)], CAT, ENV, conn=self.conn, allow_unverified=True)
        self.assertEqual(res["status"], "unverified")
        self.assertEqual(self.conn.execute("SELECT verified FROM runs").fetchone()[0], 0)

    def test_attempt_cap(self):
        res = loop.run([loop.Step("a", lambda c: 1 / 0), loop.Step("b", lambda c: 1 / 0), loop.Step("c", lambda c: 1 / 0)],
                       CAT, ENV, max_attempts=2)
        self.assertEqual(res["status"], "exhausted")
        self.assertEqual(len(res["attempts"]), 2)

    def test_emergency_stop_file_and_env(self):
        called = []
        loop.request_stop()
        res = loop.run([loop.Step("a", lambda c: called.append(1), verify=lambda r, c: True)], CAT, ENV)
        self.assertEqual(res["status"], "stopped")
        self.assertEqual(called, [])
        loop.clear_stop()
        os.environ["ADAPTIVE_STOP"] = "1"
        self.assertEqual(loop.run([loop.Step("a", lambda c: 1, verify=lambda r, c: True)], CAT, ENV)["status"], "stopped")
        os.environ.pop("ADAPTIVE_STOP")
        self.assertEqual(loop.run([loop.Step("a", lambda c: 1, verify=lambda r, c: True)], CAT, ENV)["status"], "ok")

    def test_ctx_reported_tokens_are_stored(self):
        def fn(ctx):
            ctx.update(in_tok=120, out_tok=30, wait_ms=5.0)
            return 1
        loop.run([loop.Step("a", fn, verify=lambda r, c: True)], CAT, ENV, conn=self.conn)
        row = self.conn.execute("SELECT in_tok, out_tok, wait_ms, model_ms FROM runs").fetchone()
        self.assertEqual((row[0], row[1], row[2], row[3]), (120, 30, 5.0, None))


def env_json(ok=True, **data):
    return json.dumps({"version": 1, "ok": ok, "command": "x", "data": data} if ok else {"version": 1, "ok": False, "command": "x", "error": data})


class AdapterTests(unittest.TestCase):
    def runner(self, replies):
        calls = []

        def run(args, timeout_s):
            calls.append(args)
            r = replies.pop(0)
            if isinstance(r, Exception):
                raise r
            return 0, r, ""
        run.calls = calls
        return run

    def test_scoped_snapshot_args_and_ok(self):
        r = self.runner([env_json(snapshot_id="s1", ref_count=3, complete=True, tree={"role": "window", "children": [{"role": "button", "name": "OK", "ref_id": "@s1:e2"}]})])
        ad = ui_adapter.AgentDesktop(runner=r)
        s = ad.snapshot("Notepad", root="@s0:e3", skeleton=True)
        self.assertTrue(s["ok"])
        self.assertEqual(r.calls[0], ["snapshot", "--app", "Notepad", "-i", "--compact", "--skeleton", "--root", "@s0:e3"])
        self.assertEqual(ad.resolve(s["tree"], "button", "ok"), "@s1:e2")

    def test_too_large_snapshot_falls_back(self):
        ad = ui_adapter.AgentDesktop(runner=self.runner([env_json(snapshot_id="s1", ref_count=5000, tree={})]))
        s = ad.snapshot("Unity")
        self.assertFalse(s["ok"])
        self.assertEqual(s["fallback"], "scope_or_vision")

    def test_failure_and_missing_binary_fall_back_to_vision(self):
        ad = ui_adapter.AgentDesktop(runner=self.runner([FileNotFoundError()]))
        self.assertEqual(ad.snapshot("X")["fallback"], "vision")
        ad2 = ui_adapter.AgentDesktop(runner=self.runner([env_json(False, code="PERMISSION")]))
        self.assertEqual(ad2.snapshot("X")["reason"], "PERMISSION")

    def test_bare_or_invalid_ref_rejected_locally(self):
        r = self.runner([])
        ad = ui_adapter.AgentDesktop(runner=r)
        self.assertEqual(ad.click("@e8")["fallback"], "vision")
        self.assertEqual(r.calls, [])
        self.assertEqual(ad.snapshot("X", root="e3")["reason"], "invalid root ref")

    def test_stale_ref_recovers_once_when_safe(self):
        stale = env_json(False, code="STALE_REF", disposition={"retry": "safe"})
        snap = env_json(snapshot_id="s2", ref_count=1, tree={"children": [{"role": "button", "name": "Save", "ref_id": "@s2:e9"}]})
        r = self.runner([stale, snap, env_json(clicked=True)])
        out = ui_adapter.AgentDesktop(runner=r).click("@s1:e4", app="Editor", role="button", name="Save")
        self.assertTrue(out["ok"] and out["recovered"])
        self.assertEqual(r.calls[-1], ["click", "@s2:e9"])

    def test_stale_ref_not_retried_when_unsafe(self):
        r = self.runner([env_json(False, code="STALE_REF", disposition={"retry": "unsafe"})])
        out = ui_adapter.AgentDesktop(runner=r).click("@s1:e4", app="Editor", role="button", name="Save")
        self.assertFalse(out["ok"])
        self.assertEqual(len(r.calls), 1)

    def test_timing_log_and_timeout(self):
        import subprocess
        ad = ui_adapter.AgentDesktop(runner=self.runner([subprocess.TimeoutExpired("agent-desktop", 1)]))
        self.assertEqual(ad.snapshot("X")["fallback"], "vision")
        self.assertEqual(ad.log[0]["why"], "timeout")

    def test_non_json_output_is_safe(self):
        ad = ui_adapter.AgentDesktop(runner=self.runner(["garbage"]))
        self.assertEqual(ad.snapshot("X")["fallback"], "vision")


class MetricsTests(unittest.TestCase):
    def test_usage_dedup_and_unknown(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "t.jsonl")
            u = {"input_tokens": 10, "output_tokens": 5, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 50}
            with open(p, "w") as f:
                for mid in ("m1", "m1", "m2"):
                    f.write(json.dumps({"type": "assistant", "message": {"id": mid, "usage": u, "content": "secret text"}}) + "\n")
            r = metrics.transcript_usage(p)
            self.assertEqual((r["in_tok"], r["out_tok"], r["cache_tok"], r["messages"]), (20, 10, 300, 2))
            q = os.path.join(d, "n.jsonl")
            open(q, "w").write(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
            n = metrics.transcript_usage(q)
            self.assertEqual((n["status"], n["in_tok"]), ("UNKNOWN", None))
        finally:
            shutil.rmtree(d)


SKILL = '---\nname: demo\ndescription: "Demo skill used for tests. Use when testing the proposal helper."\ntriggers: demo\n---\n\n# Demo\nAlways verify first. Safety rule stays.\n'
PROP = {"category": "windows.form_ui", "env": "app=x", "hierarchy_first": "a", "winner": "b",
        "evidence": {"a": {"n_eff": 25, "p": 1, "lb": 0.9, "lat_ms": 900}, "b": {"n_eff": 30, "p": 1, "lb": 0.93, "lat_ms": 300}}}


class SkillUpdateTests(Base):
    def setUp(self):
        super().setUp()
        self.skills = os.path.join(self.home, "skills")
        os.makedirs(os.path.join(self.skills, "demo"))
        self.md = os.path.join(self.skills, "demo", "SKILL.md")
        open(self.md, "w", encoding="utf-8").write(SKILL)

    def test_no_permission_no_change(self):
        r = skill_proposals.apply(PROP, self.skills, "demo", allow_skill_edit=False)
        self.assertFalse(r["applied"])
        self.assertEqual(open(self.md, encoding="utf-8").read(), SKILL)

    def test_apply_adds_learned_block_keeps_mandatory_text_and_rolls_back(self):
        r = skill_proposals.apply(PROP, self.skills, "demo", True, score_fn=lambda *_: 100)
        self.assertTrue(r["applied"])
        text = open(self.md, encoding="utf-8").read()
        self.assertIn("Always verify first. Safety rule stays.", text)
        self.assertIn(skill_proposals.START, text)
        skill_proposals.apply(PROP, self.skills, "demo", True, score_fn=lambda *_: 100)  # idempotent: one block only
        self.assertEqual(open(self.md, encoding="utf-8").read().count(skill_proposals.START), 1)
        rb = skill_proposals.rollback(self.skills, "demo")
        self.assertTrue(rb["restored"])
        self.assertIn(skill_proposals.START, open(self.md, encoding="utf-8").read())  # latest backup = state before 2nd apply
        # first backup restores the pristine text
        root = os.path.join(self.home, "skill-backups")
        first = sorted(os.listdir(root))[0]
        self.assertEqual(open(os.path.join(root, first, "demo", "SKILL.md"), encoding="utf-8").read(), SKILL)

    def test_score_drop_restores_automatically(self):
        scores = iter([100, 60])
        r = skill_proposals.apply(PROP, self.skills, "demo", True, score_fn=lambda *_: next(scores))
        self.assertFalse(r["applied"])
        self.assertEqual(open(self.md, encoding="utf-8").read(), SKILL)

    def test_propose_requires_enough_evidence(self):
        env = "os=windows|app=x"
        cat = "windows.form_ui"
        add(self.conn, "ui_automation_scoped", 25, lat=900, env=env, cat=cat)
        add(self.conn, "screenshot_vision", 3, lat=100, env=env, cat=cat)
        self.assertEqual(skill_proposals.propose(self.conn, classify.taxonomy()), [])
        add(self.conn, "screenshot_vision", 25, lat=300, env=env, cat=cat)
        out = skill_proposals.propose(self.conn, classify.taxonomy())
        self.assertEqual(out[0]["winner"], "screenshot_vision")


if __name__ == "__main__":
    unittest.main()
