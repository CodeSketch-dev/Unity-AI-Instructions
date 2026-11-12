---
name: skill-test-loop
description: "Test-fix-retest loop for editing a skill: static lint, optional spec check, snapshot, edit, re-score, keep or revert on score change. Use when creating or changing any SKILL.md, before publish, or when a skill misleads agents."
triggers: test skill, skill lint, improve skill, skill score, keep or revert, retest, skill regression, sua skill, kiem tra skill, cham diem skill
---

# Skill test loop

A skill edit is a code change: it gets tested. This loop is cheap (no model call) and catches structural and coverage regressions; behaviour is proven by the eval harness.

## Loop
1. Baseline: `py -I tools/skillkit/skill_loop.py snapshot skills <name>` (saves SKILL.md and score to `.skill-loop/<name>/`, git-ignored).
2. Optional spec: `tools/evals/skill-specs/<name>.json` with `must_contain` regexes (the rules that must stay), `must_not_contain` (project names, local paths), `triggers_any` (words a user would say). Add one when a mistake was caused by the skill; each spec line costs 10 points when it fails.
3. Edit the skill (keep it short; detail to `references/`).
4. Re-score: `py -I tools/skillkit/skill_loop.py score skills <name>` and the full lint `py -I tools/skillkit/skill_lint.py skills` (0 errors required).
5. Decide: `py -I tools/skillkit/skill_loop.py decide skills <name>` prints KEEP when the score did not drop, REVERT when it did; add `--apply` to restore the baseline file. A revert means: read the failed lines, change the approach, repeat from step 3. Max 3 rounds, then log the blocker.
6. Behaviour check for important skills: run the matching `tools/evals/trigger-*` grader or the skill-evals harness with and without the skill; a skill that does not change the result is deleted or merged (`skill-quality-rubric`).
7. Publish through the repo publish script; note the score before/after in the LOG.

## Score
100 minus 25 per lint error, 5 per own lint warning (collisions with other skills excluded), 10 per failed spec line. A pass proves the written instructions are well formed and cover the cases, not that an agent obeys them.

## Rules
- Never edit a skill another writer is editing (check the writers' report files first); merge on top of their version.
- Skills stay generic: no project names, no absolute local paths.
- Fix the shared source (skill, hook, audit rule) for a repeated mistake, not just the instance.
