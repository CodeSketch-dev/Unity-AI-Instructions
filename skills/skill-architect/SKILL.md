---
name: skill-architect
description: "Create, audit, fix and optimise Agent Skills (SKILL.md): inventory, spec check, backup and dependency scan, trigger tests, publish. Use when asked to create, review, merge, rename, delete or tune any skill, or when a skill never fires or misfires."
triggers: skill architect, create skill, new skill, make a skill, audit skills, skill inventory, skill spec, agent skills, agentskills, skill trigger, skill not firing, skill khong chay, tao skill, kiem ke skill, sua skill, toi uu skill, quan ly skill, skill creator, my skills, skill frontmatter, skill description, never fires, skill fires, duplicate skills, merge skills, rename skill, delete skill, skill spec, sua skill hu
---

# Skill architect

Single entry point for the lifecycle of skills. It orchestrates existing tools; it does not replace them.
Detail lives in `references/` (load only the file the current step needs). Scripts run with `py -I`.

## Hard rules
- Vendor skills (`anthropic-skills:*`, plugin caches under `~/.claude/plugins`, anything not in this repo's `skills/`) are READ-ONLY. To change one, create an own skill that extends it and say so. Never clone `anthropics/skills`; read single files on demand (WebFetch raw URL) and note the idea, not a copy.
- Before editing, renaming, merging or deleting an own skill: `scripts/backup_deps.py backup <name>` then `deps <name>`; fix every dependent (router, hooks, evals, other skills) in the same change.
- Skills are generic (no game/class names), short (body well under 500 lines, ideally under ~100), and load detail progressively: metadata -> body -> `references/` / `scripts/` / `assets/`, one level deep.
- No claim of "fires correctly" without `scripts/trigger_eval.py` output; no claim of "works" without a behaviour eval run (see Test).

## Workflow
1. **Inventory**: `py -I skills/skill-architect/scripts/inventory.py` (own + user + vendor, spec errors, missing referenced paths, token estimate). Add `--only <name>`.
2. **Find a pattern**: check `skills/INDEX.md` for an existing skill first (merge beats a near-copy); then at most 1-2 vendor examples by fetching only the needed `SKILL.md` (see `references/anthropic-patterns.md` for which). Spec rules: `references/spec-essence.md`.
3. **Draft or edit** (`references/authoring-checklist.md`): description = what + `Use when ...` + concrete user words, slightly assertive; `triggers:` in English + Vietnamese without accents; optional `not:` negative phrases to stop misfires; imperative steps; one verification line.
4. **Test** (cheap -> expensive):
   - static: `py -I tools/skill_lint.py skills` (0 errors) and `inventory.py --only <name>`;
   - routing: add 6+ labelled queries to `evals/skill-architect/trigger-queries.json` (should-fire plus near-miss should-not), run `py -I skills/skill-architect/scripts/trigger_eval.py --skill <name>` after `py -I tools/build_skill_router.py skills data/skill_router.json`;
   - behaviour: add `evals/trigger-<name>/` (prompt that does not name the skill + grader criteria) and `evals/skill-specs/<name>.json`; for important skills run with vs without the skill (see `skill-quality-rubric`, `skill-test-loop`).
5. **Iterate**: change one thing, re-score; keep on equal-or-better, revert otherwise (`tools/skill_loop.py`). Max 3-4 rounds.
6. **Publish**: `cmd //c "<repo>\publish.bat" "<msg>"` in the background (lint, index, router, sync, push). Report: files changed, lint totals before/after, trigger pass count, what was NOT verified.

## Creation priorities for this studio
Unity, FishNet multiplayer, Windows automation, game design, software testing. Before creating one, search `skills/INDEX.md` for the topic (many exist: unity-*, fishnet-*, qa-*, gdd-*, recipe-*) and extend instead of duplicating.

## Report format
`Inventory: own N (errors E, warns W) | Changed: ... | Backup: .skill-backups/<ts> | Deps fixed: ... | Lint: x->y | Trigger eval: p/n | Behaviour eval: run/not run | Unverified: ...`
