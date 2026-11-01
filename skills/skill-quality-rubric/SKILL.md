---
name: skill-quality-rubric
description: "Score, lint, test and improve a SKILL.md: structural checklist, behavioural eval spec, test-fix-retest loop with keep/revert on score. Use when writing, reviewing or tuning a skill or adding an evals/ spec."
triggers: skill quality, skill rubric, skill lint, skill test, improve skill, eval spec, skill review, kiem tra skill, cai thien skill, danh gia skill, viet skill
---

# Skill quality rubric

Use when a skill is new, edited, mis-triggers, or is never loaded.

## 1. Structural checklist (score 1 point each, target 8/8)
1. Frontmatter has `name` (= folder), quoted `description` of 20-300 chars starting with what it does and containing `Use when ...`.
2. `triggers:` lists English and Vietnamese-without-accents keywords a user would really say.
3. Body under ~120 lines; heavy material moved to `assets/` or `references/`.
4. Steps are imperative and ordered; a checklist exists for anything verifiable.
5. No project, game or class names (project contracts belong in that project AGENTS.md).
6. Verification names a concrete check (Console, MCP tool, test, screenshot), not "make sure it works".
7. No interactive prompts; the skill says "decide, log, continue" for small choices.
8. No overlap: description does not share a 6-word shingle with another skill (`py -I tools/skill_lint.py skills`).

## 2. Behavioural spec
Write 3-5 one-line scenarios: a prompt, the expected skill choice, and 2-3 observable behaviours (what it reads, what it refuses to do, what it reports). Include one negative prompt where the skill must NOT fire.

## 3. Add an evals/ spec
Copy an existing `evals/trigger-*` folder to `evals/trigger-<topic>/`:
- `prompt.md`: frontmatter `max_turns`, `allowed_tools: [Read, Glob, Grep, Skill]`, then one natural-language prompt that does not name the skill.
- `graders/criteria.md`: frontmatter `type: llm`, `weight: 1`, then one paragraph: which skill must be consulted first and the 2-3 behaviours that prove it was followed.

## 4. Test-fix-retest loop
1. Baseline: run the lint and the eval; record the score (structural points + eval pass/fail).
2. Change ONE thing (sharpen description, add trigger, trim body, add a missing step).
3. Re-run. Score up: keep. Same or down: revert that change.
4. Stop at 8/8 structural and eval pass, or after 4 iterations; log remaining gaps in the final note.

## Red flags
Vague description ("helps with X"), triggers copied from the description only, a body that restates framework docs, a skill nobody can falsify.
