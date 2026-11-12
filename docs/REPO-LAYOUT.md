# Repo layout and authoring standard (every agent, Claude Code and Codex)

This repo is the studio brain: instructions, skills, hooks and lint rules that `sync.bat` installs into Claude, Codex and every Unity project. `publish.bat` refuses to publish when this layout or the lint tests break (`tools/publish_gate.py`).

## Where things go

| Kind | Location | Rule |
|---|---|---|
| Always-on instructions | `AGENTS.md`, `STUDIO-BRAIN-DIGEST.md` | Short standing rules only. Detail goes into a skill. |
| Skill | `skills/<kebab-name>/SKILL.md` (+ `scripts/`, `references/`) | Frontmatter `name`, `description` starting `Use when`, `triggers:` incl. Vietnamese without accents. Generic, no game names. |
| Lint rule (code anti-pattern) | `lint/rules/<snake_name>.py` + `lint/tests/fixtures/bad_/good_*.cs` + test | The message must name `.claude/skills/<skill>/SKILL.md`. See skill `capture-pattern-with-lint`. |
| PowerShell hook script | `hooks/ps1/` | ASCII only. Installed FLAT into `~/.claude/pipeline-hooks/hooks/` by `sync.bat`; never rename. |
| Plugin hooks (Python) | `hooks/hooks.json`, `hooks/scripts/` | Claude plugin contract, do not move. |
| Data read by hooks | `data/` (`skill_router.json` generated, `studio_rules.json`) | Never hand-edit the router. |
| Agents, commands, templates, evals | `agents/`, `commands/`, `templates/`, `evals/` | |
| Repo tooling and its tests | `tools/`, `tools/tests/` | |
| Plans, notes, ledger | `docs/` (`docs/superpowers/plans/`, `docs/owner-requests.md`) | |

Repo root holds only: `AGENTS.md`, `README.txt`, `STUDIO-BRAIN-DIGEST.md`, `publish.bat`, `sync.bat`, `projects.txt`, `.gitignore` and the folders above. Anything else is a layout violation (`python tools/repo_layout_lint.py`).

## Workflow when you learn something reusable
1. Prose lesson -> update the matching skill (or add one). Code pattern a regex can catch -> also a lint rule (`capture-pattern-with-lint`).
2. `python -m pytest lint/tests tools/tests -q` and `python tools/repo_layout_lint.py`.
3. `publish.bat "<message>"` (lint, index, router, gate, sync, commit, push). Never edit generated `skills/INDEX.md` or `data/skill_router.json` by hand.

## Rules that save you a day
- Synced Unity projects get skills in `.claude/skills/`, lint in `.claude/lint/`; all of `.claude/` is git-ignored there. Lint messages therefore use `.claude/skills/...` paths.
- Hook installs are flat; moving a hook file needs `sync.bat` to copy it (see skill `studio-hook-factory`, "Moving or restructuring hook files").
- In shell-written source never type double backslashes (heredocs collapse them); use `chr(92)` or the Write tool.
