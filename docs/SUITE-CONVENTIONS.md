# Suite conventions

Rules for every skill, rule, recipe, tool and data file in this suite. Enforced where possible by `py -I tools/skill_lint.py [--strict] skills` (tests: `py -I -m unittest discover -s tools/tests`). Evidence base: `docs/pipeline-catalog/MASTER-CLASSIFICATION.md`.

## Naming
- Skill folder = `name` in frontmatter = `<domain>-<topic>` in lowercase hyphens (e.g. `ui-popup-anatomy`, `econ-auto-balance`). The text before the first hyphen is the domain; `tools/skill_index.py` groups by it.
- Domain prefixes: `ui`, `econ`, `gameplay`, `char`, `world`, `qa`, `batch`, `gdd`, `framework`, `perf`, `art`, `rule`, `ads`, `asset`, `legacy`, `pipeline`. Add a prefix only when two or more skills need it.
- Class by form: RULE (short, always relevant, principle + reason), SKILL (hub with `references/`), RECIPE (step list for one feature), TOOL (script with tests), DATA (tables/JSON/YAML with sources).
- Keep the listed set small: about 20-40 hub skills; recipes live as `references/*.md` inside a hub (report 12: skill listing budget is 1% of context). A skill with side effects (build, deploy, delete) sets `disable-model-invocation: true`.

## Description rules (lint: 20-300 chars)
- Start with the use case, say when to trigger, do not start with "This skill".
- Avoid sharing long phrases with another skill; the lint reports 6-word overlaps as `trigger-collision` warnings. Resolve by narrowing one description or merging skills.

## Body rules
- Under 500 lines (lint error at 500+); aim for under 150. Put the most important steps first, because only the start of an invoked skill survives compaction (report 12).
- Explain why, not only what. Detail goes in `references/`, executable checks in `scripts/`, templates in `assets/`. Every relative link must exist (lint `missing-ref`).
- Never tell an agent to dump raw scenes, prefabs or logs; scripts summarise.

## Soft-default clause (for every mined number)
State the number as a default and add: "Default from <project/report NN>; override when the project's own reference shows otherwise." Hard rules are limited to compile, wiring, data loss and protected files.

## Citation format
`(report NN, VERIFIED|INFERRED)` after a claim; NN is the catalog report number, e.g. `(report 07, VERIFIED)`. Facts not traced to a file or doc stay INFERRED. Do not claim Editor validation unless a Unity MCP result exists.

## Idempotent tools
- Every generator or builder is keyed by name or GUID; running it twice changes nothing the second time.
- Report what changed and what was skipped; exit non-zero on failure; never save a scene or prefab another agent has claimed.
- Python is stdlib only, run with `py -I`, UTF-8, Windows paths. C# Editor tools use the installed framework APIs only.

## Framework safety
Detect `com.codesketch` vs `com.sketchengine` in `Packages/manifest.json`; never invent the other version's API. Unity projects under `C:\Unity\GitProject\*` are read-only references; ask before writing there.

## Process
- Claim files before editing and re-read before writing (AGENTS.md "never overwrite newer work").
- Append to `docs/agent-handoff.md` after touching shared areas. Commit only when the user asks.
- Regenerate `skills/INDEX.md` with `py -I tools/skill_index.py skills > skills/INDEX.md` after adding a skill.
