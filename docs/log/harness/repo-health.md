# Repo health: skills and groups

Date: 2026-11-12
Scope: `skills/` (read-only count)

## Counts

- Skills (folders holding `SKILL.md`, layout `skills/<group>/<skill>/SKILL.md`): **309**
- Groups (top-level folders under `skills/` that hold skills): **10**
  - `clone-reference`, `economy-monetization`, `gameplay`, `general`, `perf-build`, `qa-testing`, `studio-process`, `ui`, `unity-editor`, `world-art`
- Flat (ungrouped) skills at `skills/<skill>/SKILL.md`: 0

## Method

- Skill total: Grep for `^name:` across `skills/**/SKILL.md` returned 309 files. Glob `skills/*/*/SKILL.md` also reports 309.
- Group total: distinct first-level folders of the 309 SKILL.md paths.
- `skills/README.md` is a file, not a group, and is not counted.

## Notes

- The count was taken with read-only Grep and Glob. The `tools/skillkit/skill_paths.py` helper was not executed because the shell rejected the compound command.
- The count includes `studio-process/studio-harness`, which is an untracked folder in the current git status.
