---
name: studio-self-training
description: "End-of-task retro that makes the studio smarter: turn lessons into skills, merge duplicates, publish, and bootstrap new projects with sync.bat. Use at the end of every task, when the owner corrects you, or when starting a new project."
triggers: retro, self training, train agents, update skill, new skill, publish, sync.bat, new project, bai hoc, rut kinh nghiem, tu hoc, skill moi, du an moi
---

# Studio self-training (retro + bootstrap)
## Retro (every task, ~2 min)
1. List lessons: bug classes, traps, measured numbers, workflows that saved time, owner corrections, agent strengths/failures.
2. For each: does a skill already cover it? Update that skill (a line or a short step). Else create `skills/<kebab-name>/SKILL.md`: frontmatter `name`, `description` ("Use when ...", <300 chars), `triggers:` (EN + VN without accents); body <= ~40 lines, imperative, generic (no game/class names), with evidence or the verification method.
3. Merge near-duplicates, remove wrong advice, keep INDEX-friendly names.
4. `publish.bat "<message>"` (full repo path, background, read output); on exit 2 re-apply onto upstream by hand and publish again.
5. Tell the owner one line: skills added/changed.
## New project
1. Place the project beside the repo or add its folder to `data/projects.txt`.
2. Run `sync.bat /nopause`: installs rules, skills, agents, hooks, router; open a new session.
3. In the project: create `docs/feedback-notes.md`, `docs/skill-candidates.md`, `docs/agent-handoff.md` on first use; project-only contracts go in its `AGENTS.md`, reusable ones go to the shared skills.
## Token habits
Index first, 1-3 skills, narrow greps, compact tool output (cap `max_chars`), batch tool calls, delegate code to the hub, never re-read what you just wrote.

## Reminder (not a gate)
The prompt-router hook adds a one-line self-training reminder to every prompt (also in sessions started before this rule). Nothing blocks you: when a task taught something reusable, update or create the skill and run `publish.bat`; if not, just finish.


## How the agent memory is wired (owner question 2026-11-10)
Three layers keep AGENTS.md in the agent's head: (1) the global `~/.claude/CLAUDE.md` block + the project `CLAUDE.md` (`@AGENTS.md`) are loaded at session start; (2) the SessionStart hook `studio_brain_digest.ps1` (registered by `tools/sync/sync_claude_setup.ps1` for startup / resume / clear / compact) re-injects `STUDIO-BRAIN-DIGEST.md` + the live `UI REFLEXES` section of AGENTS.md; (3) per-user auto-memory files (`feedback_*.md`) for owner corrections. On another machine: `git pull` the instructions repo, run `sync.bat /nopause`, open a NEW session. Keep the digest short (<= 45 lines) and update it whenever a new standing rule is added.
