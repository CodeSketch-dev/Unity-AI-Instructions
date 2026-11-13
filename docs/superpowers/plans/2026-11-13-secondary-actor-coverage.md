# Whole-scene reference coverage update

> **For agentic workers:** use the existing clone research skill and preserve evidence tags; this task updates guidance only.

**Goal:** Make clone research explicitly inventory and verify visible background/secondary actors, autonomous motion, output emitters, and their sound cues.

**Approach:** Extend `clone-research-autonomy`'s focus-pass and coverage contract; add a skill spec and one trigger evaluation. Do not create a new skill, global rule, or project-specific example.

**Acceptance:** Skill score has no errors/warnings/spec failures; trigger prompt is generic and does not name the target skill; focused regression checks require full secondary-actor/output sequence evidence and prohibit inference from primary-mechanism source alone.

Ruling: foundation = **no**. This applies to reference-clone research, not every game task; keep it inside the existing routed skill. The current audit miss is the baseline failure: the primary mechanism was studied, but a background autonomous actor and reward emission were omitted from coverage.

## Steps

- [ ] Add the skill spec and trigger evaluation first; confirm the current skill fails the new coverage requirements.
- [ ] Add concise whole-scene inventory and complete-sequence verification to the skill.
- [ ] Re-run skill score/lint and the focused trigger checks; run repository lint/tests.
- [ ] Publish from this isolated clone and independently verify the remote SHA.
