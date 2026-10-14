---
name: rule-qa-validity
description: "Avoid false QA verdicts: time scale, polluted saves, unmeasured constants, mock purchases, other agents in Play Mode. Use before trusting or reporting any test, balance or playtest result."
---

# QA validity rules

These came from real false negatives and false positives (report 11 notes/handoff). A QA result is only valid if the setup was.

1. **timeScale = 1** for verdicts. A run at timeScale 60 reported a pet lifetime of 0.7 s real; fast-forward is for exploring only and its output is never a pass.
2. **Clean save** for progression claims. A polluted save produced false completion times; start from a fresh save, or back up the dev save before mock purchases and restore after.
3. **Measure constants first** (clip length, tick interval) before auditing code that depends on them; a first audit used a provisional constant and was wrong.
4. **One Editor, one writer**: another agent entering Play Mode blocked compile three times, and two agents editing the same builder collided. Check the handoff log and Unity state before Play (`multi-agent-coexistence`).
5. **Log every temporary constant** (debug speed, TEMPORARY values) with an owner and a revert step; leftovers shipped (timeScale 20, maxAllowedTimestep 0.333) (`projectsettings-baseline` catches them).
6. **Build gate**: do not tell the user to build for a device until audit, wiring, tests and a timeScale=1 Play pass are done (`done-means-wired`).
7. Say what was NOT checked: Editor-only vs device, which locales, which aspect ratios. Pass wording needs evidence (`profiling-evidence`).
8. A red test unrelated to your change is reported, not hidden; do not edit another agent's failing files to turn it green.

Procedure and matrices: `unity-qa-playtest`; fix-retest loop with iteration caps comes with the QA harness (report 17).
