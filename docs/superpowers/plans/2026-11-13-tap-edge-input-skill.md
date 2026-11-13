# Mobile tap-edge guidance promotion

> **For agentic workers:** apply the existing mobile-input skill; preserve continuous-hold behavior while adding discrete-edge coverage.

**Goal:** Ensure Unity gameplay code does not drop a discrete touch action when press and release are observed in one input update.

**Architecture:** Extend `mobile-input-controls`, add a concise always-on contract and a prompt-hook reminder, and add a skill spec plus one focused trigger scenario. Keep this guidance generic; it does not claim that the current Android build has been verified.

**Tech Stack:** Markdown skills, JSON skill spec / studio rules, existing skill lint and evaluation conventions.

**Global Constraints:** Preserve finger identity and UI-vs-world blocking; preserve explicit hold/repeat semantics; do not claim hardware verification from a synthetic Input System test.

**Review Focus:**
- A down and up inside one input update still dispatches the discrete action once.
- The following update cannot repeat the action without new input.
- UI exclusion uses the same touch identity/edge semantics as gameplay capture.
- Continuous hold remains held-state driven where intended.

Ruling: foundation = **yes**. Discrete tap delivery is a cross-game input contract; one-line AGENTS guidance and a prompt-injected rule accompany the existing routed skill. No regex lint is suitable because valid behavior depends on whether an action is discrete or held.

## Task 1: Extend the existing skill and verification contract

**Files:** `skills/gameplay/mobile-input-controls/SKILL.md`, `tools/evals/skill-specs/mobile-input-controls.json`, `tools/evals/triggers/trigger-mobile-input-controls/{prompt.md,graders/criteria.md}`.

- [ ] Write the skill spec and trigger scenario first; run the existing skill score to verify the current skill fails the new required clauses.
- [ ] Add the shortest actionable tap-edge guidance, preserving finger/UI identity and hold semantics.
- [ ] Re-run skill score and skill lint; confirm required clauses are covered.

## Task 2: Make the rule automatic

**Files:** `AGENTS.md`, `data/studio_rules.json`.

- [ ] Add one compact always-on rule and one prompt-match injection.
- [ ] Validate JSON, the trigger route, and the repo's full required lint/test suite.

## Task 3: Publish and verify

- [ ] Run the full-path `publish.bat` for this isolated clone only after validation.
- [ ] Verify publication's remote SHA and record the result; do not claim rebuilt-device success.
