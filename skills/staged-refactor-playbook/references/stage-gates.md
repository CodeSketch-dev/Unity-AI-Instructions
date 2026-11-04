# Stage gates: exact checks and how to run them

| # | Gate | How (tool) | Pass condition |
|---|---|---|---|
| G1 | Compile | refresh assets, `console-get-logs` (errors) | 0 compile errors, no new warnings of the touched files |
| G2 | EditMode suite | `tests-run` EditMode, full | PASS >= baseline, SKIP <= baseline, FAIL 0; a rename that makes tests skip is a failure |
| G3 | Missing scripts | Editor script over scenes + prefabs: `GameObjectUtility.GetMonoBehavioursWithMissingScriptCount` | 0 on touched assets (0 everywhere before the final stage) |
| G4 | Missing references | same script, `SerializedObject` property walk for null object references with a non-zero fileID, plus pink-material check | 0 on touched assets |
| G5 | Scene reopen | open each touched scene from disk (not the cached instance), count roots | roots <= 20, no tool-marker roots, GameSingleton-class root present once |
| G6 | Play smoke | enter Play on each touched scene, wait 5 s, `console-get-logs` | no exceptions, no errors; claim blocking popups with a real tap first |
| G7 | Repeated scene flow | Home -> mode -> Home x3 (`scene-teardown-safety`) | no duplicate singletons, no leaks, no static events left |
| G8 | Visual | game-view screenshot at the reference size; parity diff when materials/maps changed | UI audits at 0 violations; parity thresholds met |
| G9 | Perf | draw calls / SetPass / batches / frame time on the main scenes in Play | not worse than baseline (say "not measured on device") |
| G10 | Lean | `size_report.py`, `import_audit.py` | MB and counts not worse; budgets in the rubric |
| G11 | Rubric | verify commands for the touched groups | no new F; failing blockers shrink |
| G12 | Git | `git status`, `git check-ignore -v` for new folders | only intended files changed; nothing important ignored; one batch = one logical change |

Rules
- Gates run in this order; stop at the first red one.
- Evidence is a number or a file path (log, CSV, screenshot), never "looks fine".
- A gate that cannot be run (no Editor, no device) is reported as NOT VERIFIED, and the dependent stage item is not marked done.
- Compare against the baseline file, not against memory.
- Time-box Editor holds: prepare scripts and expected outputs first, hold the lock only for execution, analyse the evidence after releasing.
