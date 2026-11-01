---
name: regression-suite
description: "Choose and run the right regression checks after each change class (code, prefab/UI, balance, assets, settings) with EditMode, PlayMode and screenshot evidence, kept fast. Use after any change or when picking what to test."
triggers: regression suite, regression test, what to test, run tests after change, smoke tests, kiem thu hoi quy, chay test, can test gi
---

# Regression suite

Use to decide the smallest test set that still proves nothing broke.

## Matrix (cheapest first, stop at the first real failure)
| Change class | Run |
|---|---|
| Pure logic / formulas | EditMode tests for the module, then full EditMode |
| Data / save fields | EditMode migration test with an old save, load-save-load roundtrip |
| Balance / economy | simulator or economy test; compare pacing to the stored baseline |
| Prefab / UI | layout audit on touched prefabs, Play screenshot at the primary and one alternate aspect, press/feedback check |
| Scene / world | missing-script count, Play 5 s with empty Console, entry-to-exit path |
| Assets / import / shaders | refresh, Console clean, one Play capture |
| Settings / packages | compile, full EditMode, short PlayMode smoke |
| Pooling / lifecycle | quick `soak-test` plus scene reload loop |

## Steps
1. Classify the change from the diff; pick rows.
2. Compile first; read the Console; fix compile errors before any test.
3. Run EditMode via tests-run (or the project result-writer if the runner times out). Record PASS and SKIP counts and compare with the last green run.
4. Run the PlayMode smoke from the real entry flow; capture screenshots to a named folder.
5. Classify each failure: caused by this change or pre-existing (show evidence). Fix yours at once.
6. After a Play session with domain reload off, reload scripts before the next EditMode run if the project notes say statics leak.

## Keeping it fast
Tag slow tests and run them only for rows that need them; reuse one Play session for several checks; never re-run a green stage after a fix that cannot affect it; store the last green counts in the status doc.

## Report
Change class, rows run, counts before/after, failures with classification, evidence paths.
