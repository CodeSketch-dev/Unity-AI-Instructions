# Repo layout and authoring standard (every agent, Claude Code and Codex)

This repo is the studio brain: instructions, skills, hooks and lint rules that `sync.bat` installs into Claude, Codex and every Unity project. `publish.bat` refuses to publish when this layout or the lint tests break (`tools/publish/publish_gate.py`). The rule is enforced by `tools/publish/repo_layout_lint.py`: **no folder holds more than 15 entries** (exemptions are listed in that file with a reason), and the repo root holds only the items below.

## Map

```
AGENTS.md  README.txt  STUDIO-BRAIN-DIGEST.md  publish.bat  sync.bat      (root files)
skills/      one folder per skill (Claude/Codex discover skills one level deep)
agents/ commands/   Claude plugin definitions (loaded one level deep)
hooks/       hooks.json + scripts/ (plugin, do not move) + ps1/ (PowerShell hook scripts)
data/        skill_router.json (generated), studio_rules.json, projects.txt, skill-overrides.snippet.json, templates/
tools/
  publish/   publish.ps1, publish_gate.py, repo_layout_lint.py
  sync/      sync_claude_setup.ps1, install_project_lint.ps1, install_hooks.py
  skillkit/  skill_lint.py, skill_index.py, build_skill_router.py, skill_loop.py, skill_budget.py, hubs.txt
  lint/      Lint-Triggered Skills engine: engine.py, run_lint.py, rules/, tests/
  evals/     triggers/ (one case per skill), skill-architect/, skill-specs/, adaptive/
  adaptive/  adaptive-task-intelligence tooling
  packages/  self-contained helper apps
  tests/     pytest suite for the repo tooling (flat on purpose)
docs/
  owner-requests.md  feedback-notes.md  agent-handoff.md  REPO-LAYOUT.md   (conventional ledgers + this file)
  guides/ log/ catalog/ research/ skill-scenarios/<group>/ superpowers/{plans,specs}/
```

## Where things go

| Kind | Location | Rule |
|---|---|---|
| Always-on instructions | `AGENTS.md`, `STUDIO-BRAIN-DIGEST.md` | Short standing rules only. Detail goes into a skill. |
| Skill | `skills/<kebab-name>/SKILL.md` (+ `scripts/`, `references/`) | Frontmatter `name`, `description` starting `Use when`, `triggers:` incl. Vietnamese without accents. Generic, no game names. |
| Lint rule (code anti-pattern) | `tools/lint/rules/<snake_name>.py` + `tools/lint/tests/fixtures/bad_/good_*.cs` + test | The message must name `.claude/skills/<skill>/SKILL.md`. See skill `capture-pattern-with-lint`. |
| PowerShell hook script | `hooks/ps1/` | ASCII only. Installed FLAT into `~/.claude/pipeline-hooks/hooks/` by `sync.bat`; never rename. |
| Plugin hooks (Python) | `hooks/hooks.json`, `hooks/scripts/` | Claude plugin contract, do not move. |
| Data read by hooks or sync | `data/` | Never hand-edit `skill_router.json`. |
| Repo tooling | `tools/<group>/` | Add a script to the group it belongs to; a new group only when none fits. |
| Plans, notes, research | `docs/<group>/`; dated plans and specs in `docs/superpowers/` | The three ledger files stay at `docs/` root. |

## Workflow when you learn something reusable
1. Prose lesson -> update the matching skill (or add one). Code pattern a regex can catch -> also a lint rule (`capture-pattern-with-lint`).
2. `python -m pytest tools/lint/tests tools/tests -q` and `python tools/publish/repo_layout_lint.py`.
3. `publish.bat "<message>"` (lint, index, router, gate, sync, commit, push). Never edit generated `skills/INDEX.md` or `data/skill_router.json` by hand.

## Rules that save you a day
- Synced Unity projects get skills in `.claude/skills/`, lint in `.claude/lint/`; all of `.claude/` is git-ignored there. Lint messages therefore use `.claude/skills/...` paths.
- Hook installs are flat; moving a hook file needs `sync.bat` to copy it (see skill `studio-hook-factory`, "Moving or restructuring hook files").
- After moving scripts, fix the repo-root computation (`parent.parent...`, `$PSScriptRoot`), test `sys.path` inserts and `.bat` callers: textual search-and-replace misses `%REPO%\tools\...` and `%~dp0...` forms.
- In shell-written source never type double backslashes (heredocs collapse them); use `chr(92)` or the Write tool.
