---
name: capture-pattern-with-lint
description: "Use when the owner says 'learn from this mistake', 'save this pattern', 'rut kinh nghiem' or an agent hits a repeatable anti-pattern: write a short skill, then a lint rule whose error points to it, then prove the rule fires."
triggers: save this pattern, learn from this mistake, capture pattern, lint rule, rut kinh nghiem, luu pattern, luu lai pattern, tao lint rule, anti-pattern, loi lap lai
---

# Capture a pattern as skill + lint rule

Goal: a lesson must not depend on an agent remembering it. The linter is the trigger: the violation message is a micro-prompt that sends Claude Code AND Codex to the one skill file that explains the fix. Skills cost zero startup context; they load only when the linter fires.

## Steps (all in this repo, never in a Unity project)
1. **Skill** created with `python tools/skillkit/new_skill.py <kebab-name> --group <group> --desc "Use when ..."` (lands in `skills/<group>/<kebab-name>/SKILL.md`), under ~40 lines: frontmatter (`name`, `Use when ...` description < 300 chars, `triggers:` incl. Vietnamese without accents), why it is banned, ordered fix steps with a verification, legit exceptions. No game or class names unless it is a project contract.
2. **Rule** `tools/lint/rules/<snake_name>.py` exporting `RULE = Rule(id, pattern, why, skill, require=None)`. `id` is the kebab skill/rule name, `skill` is the folder from step 1, `why` is one short sentence (the engine appends the mandatory-read path and the opt-out). Add `require=` when the pattern alone is too broad (file-level second condition). Keep it a regex over one line; do not add an AST engine for one rule.
3. **Fixtures + test** `tools/lint/tests/fixtures/bad_<name>.cs` and `good_<name>.cs`, then a test in `tools/lint/tests/` that asserts the bad fixture is flagged at the right line, the good one is clean, and `// lint-ok:<id> <reason>` suppresses. Run `python -m pytest tools/lint/tests -q` and watch the new test fail before the rule exists (TDD).
4. **Prove it**: `python tools/lint/run_lint.py <bad fixture>` must print `[RULE <id>] ... MANDATORY: read .claude/skills/<skill>/SKILL.md ...` and exit 2.
5. **Publish**: `publish.bat "<message>"` (runs layout lint, rule tests, skill lint, then syncs). Rules reach Unity projects on the next `sync.bat`.

## False-positive checklist (a rule that cries wolf gets ignored)
- Does it also match legit code (pools, Editor tools, tests)? Editor/ and Tests/ folders are already excluded; otherwise narrow the pattern or add `require=`.
- Is the message under ~300 chars and does it say what to do, not just what is wrong?
- Can an agent satisfy the rule without a hack? If the only way out is the opt-out comment, the skill steps are wrong.

## Not a lint case
A rule about behaviour, taste or process (no code pattern to match) belongs in `data/studio_rules.json` or the digest: see `studio-hook-factory`.
