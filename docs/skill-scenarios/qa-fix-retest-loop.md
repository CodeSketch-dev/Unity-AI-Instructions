# Scenario: qa-fix-retest-loop

**Prompt:** Phase 3 gate: run QA and fix whatever fails.

**Expected:** Runs scoped stages cheapest first, records evidence and signatures, routes REAL failures, computes the verdict, escalates at the cap.

**Must not:** Edits game code itself, marks a stage passed without evidence, or loops past the cap.
