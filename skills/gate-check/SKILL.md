---
name: gate-check
description: "Phase gate verdict (PASS/CONCERNS/FAIL) before moving prototype to vertical slice to content to polish to release, backed by an evidence list. Use when a phase ends, before starting the next, or on 'are we ready'."
triggers: gate check, phase gate, ready for next phase, milestone review, vertical slice, release readiness, cong kiem tra, qua giai doan, san sang phat hanh
---

# Phase gate check

Use at every phase boundary. Decide the verdict yourself from evidence, never from feelings.

## Phases and what must be true
- **Prototype -> Vertical slice**: core loop playable start to finish; one fun-test note; no blocking Console errors; chosen framework/architecture recorded.
- **Vertical slice -> Content**: one level/zone/feature at final quality (art, audio, UI, feel); save/load works; entry-to-exit path run in Play Mode; perf sampled on the slice.
- **Content -> Polish**: all planned content present and wired (`done-means-wired`); economy simulated; regression suite green; no placeholder art left in reachable screens.
- **Polish -> Release**: soak test clean; low-end perf budget met or waived with reason; ads/IAP flows checked with mocks; store-facing text/ids owned by the owner are listed, not invented; known-bug list triaged.

## Steps
1. Name the gate and read the plan/backlog for its exit criteria.
2. For each criterion collect evidence: test result, Console snapshot, screenshot path, profiler numbers, doc link. Use `test-evidence-review` if proof looks weak.
3. Mark each criterion MET / PARTIAL / MISSING.
4. Verdict:
   - PASS: all MET.
   - CONCERNS: only PARTIAL items that are low risk; list each with a fix and keep moving.
   - FAIL: any MISSING item that blocks players or data; list fixes and re-run the gate after.
5. Write the verdict to the project handoff/status doc (date, gate, evidence paths). Continue with the next phase on PASS/CONCERNS without asking; on FAIL fix first.

## Checklist
- Evidence exists for every line (path or number).
- Console free of errors from our code after a fresh Play.
- Open defects ranked; none cause data loss or crash.
