---
name: qa-static-checks
description: "No-Unity static scanners: missing scripts and references in YAML assets, banned APIs, layout and naming, asmdef and UnityEditor leaks, plus qa_run.py stage bookkeeping and verdicts. Use on every batch of edits."
---

# Static checks

Stdlib Python in `scripts/` (run with `py -I`). All accept `--project P`, `--files` (diff-scoped), `--json`; exit 1 on a hard finding. They never open Unity, so they run when the Editor is down (rung 3 of `qa-batch-and-fallbacks`) and in the PostToolUse hook.

| Script | Finds |
|---|---|
| `qa_scan_refs.py` | MISSING-SCRIPT, MISSING-REF, DANGLING-LOCAL, NULL-REQUIRED (`--required-refs` patterns) in text-serialized assets. A full scan is first-party scoped (`Assets/_Game`, falling back to `Assets`); explicit `--files` are always checked. Binary assets are skipped and counted |
| `qa_banned_api.py` | hot-path GetComponent/Find/Camera.main/Instantiate, allocating physics, PlayerPrefs, Task.Run, leftover TEMP/REVERT, timeScale writes. Scope = first-party folder; suppress one line with `// qa-allow: RULE reason` |
| `qa_lint_layout.py` | namespace, file/type name, role folders (Data/Factory/Event), serialized-field and const naming, loose files in Assets/ |
| `qa_asmdef.py` | asmdef cycles, editor asmdef flags, test asmdef constraint, `using UnityEditor` leaking into player builds |
| `qa_run.py` | `static` runs all four and records stage S2; `record` stores any stage result with evidence; `verdict` computes the verdict and writes `docs/qa/reports/` |

## Reading results
A missing GUID on a reference project often means art that was never committed there, not a scanner bug: confirm with the `.meta` search before blaming the scan. `ASMDEF-TESTS` applies only to assemblies identified as tests, not ordinary Editor tooling that merely references TestRunner. The scanners are a cheap proxy; they never claim performance.

## Wiring
The `qa_post_edit` hook runs the single-file subset after each edit and feeds hard findings back. The Stop gate (`hooks/`) expects evidence recorded through `qa_run.py record`. Per-project data: `qa/required-refs.json`, optional `qa/banned-rules.json`.
