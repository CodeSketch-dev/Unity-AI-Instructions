# Agent Skills spec essence (source: agentskills.io/specification, read 2026-11-10)

Re-fetch https://agentskills.io/specification when in doubt; this is a working summary, not a copy.

## Layout
`skill-name/SKILL.md` (required) + optional `scripts/` (executable, documented deps, clear errors), `references/` (focused docs loaded on demand), `assets/` (templates, schemas, images). Reference files with relative paths, one level deep from SKILL.md.

## Frontmatter
| field | rule |
|---|---|
| name | required, 1-64, `a-z0-9-`, no leading/trailing/double hyphen, equals folder name |
| description | required, 1-1024, says what AND when; include keywords an agent would match |
| license | optional, short name or bundled file |
| compatibility | optional, <=500, only for real environment needs |
| metadata | optional string->string map, unique key names |
| allowed-tools | optional, space separated, experimental |

House additions (this repo only, not in the spec): `triggers:` (comma list, EN + VI no accents, feeds `data/skill_router.json`), `not:` (negative phrases), description limit 300 chars, lint in `tools/skillkit/skill_lint.py`.

## Progressive disclosure budget
1. metadata ~100 tokens, always loaded;
2. SKILL.md body <5000 tokens (<500 lines), loaded on activation;
3. resources loaded only when the step needs them.

## Validation
Reference validator: `skills-ref validate ./skill` (agentskills repo). Local equivalent: `skills/skill-architect/scripts/inventory.py` + `tools/skillkit/skill_lint.py`.
