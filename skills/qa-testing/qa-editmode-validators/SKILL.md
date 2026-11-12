---
name: qa-editmode-validators
description: "EditMode data and wiring validators: config references, ranges, ids, prefab and scene wiring via attributes and reflection. Use when adding configs or prefabs, or after wiring."
---

# EditMode validators

Templates in `assets/` (uncompiled `.cs.txt`; copy into the project through the Editor or MCP, never hand-write meta files):
- `QaAttributes.cs.txt`: `[QaOptional]`, `[QaRange(min,max)]`, `[QaNonZero]`, `[QaId]`.
- `Qa_Config_Tests.cs.txt`: every ScriptableObject under `Configs/` has no null object references (unless optional), numeric fields inside range, ids unique and non-empty.
- `Qa_Wiring_Tests.cs.txt`: prefabs and scenes have no missing scripts, serialized object fields assigned, one AudioListener, an EventSystem when a Canvas exists.

## Rules for agents
- When you add a config field that must not be zero, bounded, or an id, add the attribute in the same change.
- Optional references are marked `[QaOptional]` with a comment. Silent nulls are the bug class this catches.
- Never weaken a test to pass it. A failing validator is either a real defect or a validator bug explained in the report.
- Known-red entries need an owner and an expiry date in `qa/known-red.json`; unexplained red tests block `PASS`.
- No asmdefs in the project: the test assembly reaches game types by reflection; otherwise reference the game asmdef.

## Run
MCP test runner, or headless via `qa_unity_batch.py` (`qa-batch-and-fallbacks`). Record stages S3 and S4 with the result summary as evidence.
