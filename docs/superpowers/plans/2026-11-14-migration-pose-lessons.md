# Metadata migration and full-pose preservation

**Goal:** Extend the existing reference-port skill with two reusable checks exposed by backend and transform migrations.

**Ruling:** Foundation = no. These are focused reference-port/migration checks, not universal game-process instructions. Edit only `reference-port`, its spec, and one trigger case.

**Acceptance:** Baseline spec fails before skill text changes; after change focused skill loop is 100 with no lint warnings/errors. Trigger grader covers both failures. Full instruction-repo tests and publish gates are recorded; remote HEAD is verified.

## Steps
1. Add required phrases to existing skill spec and a natural prompt/grader first; capture baseline RED.
2. Add concise generic rules: audit every metadata consumer after a backend cutover; required authored bindings fail closed; preserve full local position and rotation across split/reparent/rebase; verify asymmetric basis/corners, not only center.
3. Re-run score, diff checks, and repository tests; inspect result for game-specific names.
4. Publish from the isolated clone and fetch/compare the remote SHA.

**Verification limit:** Source-level gates only. No game code, Unity Editor operation, natural-flow test, or device proof is part of this task.
