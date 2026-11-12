---
name: studio-hook-factory
description: "Turn any manual reminder the owner repeats into automation: a data/studio_rules.json rule, a hook, an audit script or a loop, proven with a dry run. Use when the owner corrects you twice, says 'always / every time / I have to ask', or asks to automate the studio."
triggers: hook, auto hook, tu dong, luon luon, moi lan, phai nhac, thu cong, automation, studio autopilot, retro gate, correction
---

# Studio hook factory (the studio must not need to be asked)

Rule of the house: **a reminder that had to be typed twice becomes a mechanism, not a sentence.** Prose in AGENTS.md is attention; hooks and audits are enforcement.

## What already exists (keep using it)
- SessionStart `studio_brain_digest.ps1`: re-injects `STUDIO-BRAIN-DIGEST.md` + live `UI REFLEXES` on start / resume / clear / compact.
- UserPromptSubmit `studio_rules_hook.ps1 -Event UserPromptSubmit`: reads `data/studio_rules.json`; detects owner corrections ("I told you", "always", "again"...), arms the retro gate, escalates repeats ("build an audit, not prose") using `~/.claude/studio_corrections.log`.
- Stop `studio_rules_hook.ps1 -Event Stop`: the retro gate; blocks finishing (max 2x) until the skills repo (skills/, AGENTS.md, digest, data/studio_rules.json) has a new commit or change.
- Skill router + UI gate + ink audit hooks (see `ui-always`, `ui-ink-audit`).

## Decision table: how to automate a recurring reminder
| The owner keeps saying... | Build | Where |
|---|---|---|
| "remember rule X" (attitude, workflow) | one line in the digest + a matching rule object in `data/studio_rules.json` (inject text on the trigger words) | repo root |
| "every UI must have Y" (checkable in the project) | an audit that FAILS (Editor script / python) + run it from the Stop/UI gate | project Editor tools + skill template |
| "do Z whenever you touch file type F" | PreToolUse/PostToolUse rule with a path regex | `data/studio_rules.json` (event PreToolUse) |
| "check this every N minutes / overnight" | scheduled loop / cron task with a runbook skill | `studio-loop-runbook` |
| "agents forget what I decided" | decision log row in docs + digest line | project docs + digest |

## Procedure (do it in the same session, never ask)
1. Name the mechanism and its trigger (regex on the diacritics-stripped prompt, tool name + path, Stop condition).
2. Implement the smallest thing: extend `data/studio_rules.json` (new object: `id`, `event`, `match`, `inject`, `flag`) or add the audit script.
3. **Dry-run it**: pipe a sample event into the hook (`echo '{"session_id":"x","prompt":"..."}' | powershell -File studio_rules_hook.ps1 -Event UserPromptSubmit`) or run the audit on a known-bad case; show the output.
4. Add the rule to `STUDIO-BRAIN-DIGEST.md` only if it is a standing behaviour; keep the digest <= 45 lines.
5. `publish.bat` (lints, syncs, registers hooks, pushes). On other machines: `git pull` + `sync.bat /nopause`.

## Toward a fully automatic studio (roadmap the director keeps advancing)
Intake (owner message -> ledger row, automatic) -> plan (superpowers, automatic) -> parallel delegation with owned files (Codex / subagents) -> compile + bake + Play capture -> audits (layout, ink, text M/D/X, press sweep, lit-face scan) -> review -> commit/push -> retro (skills upgraded by the Stop gate). Every manual step the owner still performs is a backlog item for this skill.

## Moving or restructuring hook files (trap, learned 2026-11-12)
- Installed `settings.json` hooks point at the FLAT folder `%USERPROFILE%\.claude\pipeline-hooks\hooks\<name>.ps1` (and read `data/skill_router.json` / `data/studio_rules.json` next to the script via `$PSScriptRoot`). Repo-side moves must keep that installed layout: have `sync.bat` copy the moved scripts and data files flat into it, then parse-check. Never move a hook file and assume the installed copy follows.
- `hooks/hooks.json` + `hooks/scripts/` is a Claude plugin (`${CLAUDE_PLUGIN_ROOT}` paths): do not rename it.
- Before moving: snapshot installed file hashes and the `settings.json` hook command list; after: run sync, pipe a sample prompt into the installed hook, compare test pass/skip counts.

## Code anti-patterns
A repeatable code pattern (something a regex can catch in C#) is a lint rule, not a prose rule: use skill `capture-pattern-with-lint` (skill + `lint/rules/<name>.py` + fixtures). The linter message sends Claude Code and Codex to the skill file.
