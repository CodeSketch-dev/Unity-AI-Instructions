---
name: qa-playmode-smoke
description: "PlayMode smoke and perf capture: boot, enter each mode through its button, input bot with goals, fail on exceptions, structural perf counters compared with a baseline. Use before calling gameplay done."
---

# PlayMode smoke and perf

Templates in `assets/` (uncompiled): `Qa_Smoke.cs.txt` (boot, modes, exception gate), `IQaGoal.cs.txt`, `Qa_PerfProbe.cs.txt`. `scripts/qa_perf_compare.py` compares a capture with `qa/perf-baseline.json`.

## Smoke
- Config `qa/smoke.json`: boot scene, ready scene, allow-list of harmless log patterns, modes (button path, expected scene, seconds).
- Enter modes through the same button path a tap uses. Fail on any Exception or Error log not allow-listed, with the stack in the report.
- Validity: timeScale 1 and a known save (fresh or fixture) or the result is INCONCLUSIVE (`rule-qa-verdicts`).
- Give pickups, targets and zones an `IQaGoal` (ten lines) so the bot makes real progress. Without it the run only proves no exceptions; say so.
- After leaving a mode, read the Console again: errors on exit are real.

## Perf capture
`Qa_PerfProbe` records batches, set-pass calls, GC bytes per frame, p95 frame time and memory for a 20 s window after warm-up. Compare with the stored baseline: structural counters regress beyond a tolerance or GC grows by more than a few hundred bytes per frame means FAIL. The report says `measured_on: editor`; it is not a low-end device measurement (`profiling-evidence`, `device-tier-policy`). Updating a baseline needs the human's approval.
