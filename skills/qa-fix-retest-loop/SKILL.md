---
name: qa-fix-retest-loop
description: "Run a phase QA gate as a bounded loop: scan, test, read Console, classify failures, fix via the owning agent, retest, escalate at the cap. Use for /qa-gate or after each implementation batch."
---

# QA fix-retest loop

Setup validity comes from `rule-qa-validity`; verdict words from `rule-qa-verdicts`; scripts from `qa-static-checks`. Stage ids: S0 preflight, S1 compile, S2 static, S3 data, S4 wiring, S5 ui, S6 play, S7 perf, S8 log.

## Loop
1. **Preflight (S0):** list MCP tools, confirm project and scene, take a Console baseline, check the Editor lane claim. Pick the rung (`qa-batch-and-fallbacks`).
2. **Scope:** `.cs` -> S1 S2 S3; prefabs and scenes -> S2 S4 S5 S6; configs -> S3 S6; art or shaders -> S5 S7. A milestone runs everything.
3. **Run cheapest first** and stop at the first red stage: `qa_run.py static --scope diff`, compile and Console, EditMode (`qa-editmode-validators`), UI (`ui-validator`, `ui-visual-qa`), smoke and perf (`qa-playmode-smoke`), log triage (`unity-log-triage`).
4. **Record** each stage: `qa_run.py record --stage S3 --result pass|fail --evidence "..." --signature "..."`.
5. **Classify** failures: REAL, TEST-BUG (explain in the report, max one per iteration), ENV (retry twice with backoff, then escalate), FLAKY (rerun the single check three times; consistent pass is recorded as flaky).
6. **Route** REAL failures to the owning agent with signature and reproduction; QA never edits game code. Retest from the failed stage, then once from S1 when code changed.
7. **Verdict:** `qa_run.py verdict --task NAME --rung mcp|batch|static --save fresh|fixture`.

## Cap and escalation
- `record` warns on the second identical signature (change strategy: re-read the failing path) and on the third (escalate). Overall cap: 5 iterations, 3 for UI-only.
- Escalate also when a decision is needed (design, API, economy intent), a destructive action is required, a test would have to be weakened, or only a device can answer. Give the human one screen: verdict, the blocking item, what was tried, the smallest decision, evidence paths.

## Evidence
Pass only with an artifact: test output, Console excerpt, validator result or capture path. `qa_run.py record` and `orchestrator.py mark` refuse empty evidence.
