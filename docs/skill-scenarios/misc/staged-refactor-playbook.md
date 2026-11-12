# Scenario: staged-refactor-playbook

## Case 1

**Prompt:** Refactor a live project toward the reference architecture.

**Expected:** Takes a baseline snapshot (git clean, compile state, EditMode PASS/SKIP, missing scripts, Play 5 s, lean numbers, rubric score), then stages cheapest first.

**Must not:** Starts moving scripts without a baseline.

## Case 2

**Prompt:** A stage breaks Play.

**Expected:** Rolls back to the batch commit hash or fixes within the gate; never proceeds with a red batch.

**Must not:** Stacks the next stage on top of a red one.

## Case 3

**Prompt:** Report a batch.

**Expected:** Lists compile, EditMode PASS and SKIP counts vs baseline, missing scripts 0, Play clean, before/after lean numbers.

**Must not:** Reports looks good.

## Case 4

**Prompt:** Two minigame copies exist.

**Expected:** Merges into base + config; both are live so nothing is deleted without proof.

**Must not:** Deletes one copy as a duplicate.
