UNITY AI INSTRUCTIONS: SYNC GUIDE
=================================

Repository: https://github.com/CodeSketch-dev/Unity-AI-Instructions.git

Purpose
- AGENTS.md is the single source of truth for global instructions.
- skills\ holds the skill suite (see skills\README.md; plan: docs\guides\SKILL-SUITE-PLAN.md).
- One sync tool: sync.bat. Double-click to run; no PowerShell needed.

What sync.bat does
  AGENTS.md  ->  %USERPROFILE%\.claude\CLAUDE.md   (Claude)
  AGENTS.md  ->  %USERPROFILE%\.codex\AGENTS.md    (Codex)
  skills\*   ->  %USERPROFILE%\.claude\skills\ and %USERPROFILE%\.codex\skills\
- Clean repository: runs git pull --ff-only first. Uncommitted changes: skips pull and syncs local files.
- Differing destination files are backed up next to them (*.backup-yyyyMMdd-HHmmss). Only changed skills are updated.
- Options: /nopull (skip git pull), /nopause (no final keypress wait).

Rules
1. Edit only AGENTS.md and skills\ in this repository. Never edit .claude or .codex directly; the next sync overwrites them.
2. No tokens, API keys, keystores, passwords or credentials in the repository.
3. Open a NEW Claude/Codex session after syncing.
4. A skill deleted or renamed here must be removed by hand from .claude\skills and .codex\skills.
5. All repository content (instructions, skills, docs) is written in English to save tokens.

Daily workflow
A. Just get the latest: double-click sync.bat, then open a new session.
B. Change instructions/skills and publish:
   1. Edit AGENTS.md or files under skills\.
   2. Double-click sync.bat (syncs local edits, no pull).
   3. In a terminal at the repository: git add -A ; git diff --cached --check ; git commit -m "Update shared agent instructions" ; git push
   4. Open a new session.
C. New machine: install Git, sign in to GitHub, git clone the repository, double-click sync.bat in the clone (any path works).
D. Verify the three instruction files match (PowerShell):
     Get-FileHash ".\AGENTS.md", "$env:USERPROFILE\.codex\AGENTS.md", "$env:USERPROFILE\.claude\CLAUDE.md"

Troubleshooting
1. "git pull failed": history diverged from GitHub. Run git status, resolve (commit/rebase/merge), or run sync.bat /nopull.
2. No change after sync: you did not open a new session.
3. *.backup-* files are normal. Restore by copying one back over CLAUDE.md or AGENTS.md.
4. Claude reads a project's AGENTS.md only when the project has no CLAUDE.md. If it has one, add the line "@AGENTS.md" to it.
5. Skill helper scripts need Python on PATH. sync.bat itself does not.

NEW PROJECT / SELF-TRAINING
- Put the Unity project next to this repo (the parent folder is scanned) or add its folder to data/projects.txt, then run sync.bat /nopause. The project gets the shared rules (CLAUDE.md block + .claude/ai-instructions.md), all skills, agents, hooks and the skill router; Codex gets the same rules via ~/.codex/AGENTS.md.
- Agents train the studio themselves: at the end of every task they update or add skills (see "Studio self-training loop" in AGENTS.md and skill studio-self-training), then run publish.bat. Other agents and the other machine read those skills after sync.bat.
