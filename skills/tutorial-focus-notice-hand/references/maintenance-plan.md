# Focus skill maintenance - 2026-11-03

## Spec
Make tutorial-focus routing automatic and portable. Separate measured reference facts from historical project decisions. The center hole must reach the real action on the first completed tap; a canceled/disabled tap must never execute it. A notice alias reuses the same action rather than duplicate spend or progression logic.

Scope: this skill, its portable reference and evidence index, one trigger eval. No Unity project changes, image replacements, or historical dump rewrites.

Approach: keep the evidence archive; replace stale instructions and the standalone template. Editing prose alone would leave a contradictory template; replacing historical dumps would lose provenance. The template becomes a scene-authored view with serialized references and an adopting project's Editor builder.

Active skills: skill-quality-rubric (metadata/checks/eval), spec-then-plan (scope/acceptance), multi-agent-coexistence (isolated edits). UI skills were read during implementation; this documentation phase does not modify Unity UI.

## Plan and acceptance
- [x] Baseline: description has 302 chars and unquoted colon; lint reports two errors for this skill.
- [x] Replace main rules with generic inspect/build/input/verify steps; quote description <=300 chars and retain bilingual routing cues.
- [x] Add reference profile, input matrix and historical labels; update portable template without raw-input completion.
- [x] Add natural-language trigger eval plus positive/negative scenarios.
- [x] Lint: 0 errors repository-wide; 123 existing cross-description warnings, none involving this skill. This skill: 217 description chars, 39 body lines, 0 focused findings.
- [x] Eval structure suite: 3 tests passed. Deterministic router: 2 positive cases select this skill; 1 app-icon negative case does not. The LLM behavioral eval was authored but not executed by a runner.
- [x] Scoped git diff check passes. Root owns combined publish; no publish run from this lane.

Unity compilation, visual parity and touch behavior of the portable template are not verified by lint. The adopting project must run the Play acceptance matrix. Main integration owns runtime verification.
