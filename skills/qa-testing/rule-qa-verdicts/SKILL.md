---
name: rule-qa-verdicts
description: "QA verdict vocabulary and when each is allowed: PASS, PASS-WITH-NOTES, STATIC-PASS, INCONCLUSIVE, FAIL. Use before writing any done, pass or verified claim."
---

# QA verdicts

A verdict is computed from recorded stage evidence by `qa_run.py verdict` (qa-static-checks), not chosen by feel.

| Verdict | Meaning | May say "done"? |
|---|---|---|
| PASS | compile, static, data, wiring, play and log stages passed with evidence on a connected Editor or batch run | yes |
| PASS-WITH-NOTES | as PASS plus soft findings, each with a written reason | yes, list the notes |
| STATIC-PASS | only file scans ran; Unity was unavailable | no: say compile, wiring and play are NOT verified |
| INCONCLUSIVE | the setup was invalid (timeScale not 1, unknown save, shared Editor) or a required stage never ran | no |
| FAIL | a hard rule is red after the iteration cap or after escalation | no |

## Hard versus soft
Hard: compile errors, exceptions, missing script or reference, overlapping interactive UI, text overflow, any QA test red, performance regression beyond the stored baseline. Soft: spacing, icon/label ratios, small visual diffs. A soft finding needs a reason line; without it, it is hard.

## Validity gates
Follow `rule-qa-validity`: timeScale 1, known save, measured constants, no temporary test code left, Editor not owned by another agent, compile finished before a stage starts, generated content rebuilt and diffed (builders must be idempotent).

## Wording
Report what ran and what did not. Editor-measured numbers are labelled so; nothing is claimed about a low-end device without a device run.
