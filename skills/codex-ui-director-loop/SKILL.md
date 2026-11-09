---
name: codex-ui-director-loop
description: "Director workflow for UI work done by Codex CLI: plan doc + brief with owned files and measured defects, round files, review by Play capture and pixel measurement, protect shared helpers. Use when you delegate any UI/layout task to Codex or another coding agent."
triggers: codex, delegate ui, director, brief, owned files, giao codex, review codex, round 2
---

# Codex UI director loop

1. **Log + plan first**: owner request row (docs/owner-requests.md), plan in docs/superpowers/plans/<date>-<name>.md (goal, global constraints, review focus, tasks with owned files, acceptance numbers). The plan is shared with Codex.
2. **Brief** (docs/reports/prompt-<name>.md): project root, owned files (nothing else), read-first list (plan, screenshot by ABSOLUTE path, the AGENTS.md UI sections), helpers it may reuse with signatures, house style, "no Unity, no git", `Report file:`. Add the rule: **grep usages before removing or renaming any symbol; shared helpers used by files you do not own must stay** (a round-1 Codex deleted a shared helper and broke compile in two other files).
3. **Dispatch**: `codex exec --skip-git-repo-check -C <root> -s workspace-write --disable hooks --disable codex_hooks - < brief.md` in the background; wait on the report file (monitor loop), not on the launcher. Do not kill other codex processes (the harness classifier blocks it); queue a new round after the running one finishes.
4. **Review like a senior**: diff, compile, rebake prefabs, enter Play, capture, LOOK at the screenshot, measure (paddings, equal heights, lit-face centring, icon >= text). Write defects with numbers into the next round file (`prompt-...-r2.md`) and attach the capture path. Owner decisions that arrive mid-flight go into a REVISED round that explicitly supersedes the older brief.
5. **Finish**: EditMode green, one commit with the reports + captures in docs/reports, push. Extract skills when the owner says he is satisfied (or the standing "extract the essence" order).

6. Every brief (UI or code) carries the ARCHITECTURE LAW line: layered calls (SDK <- adapter <- decision layer), single responsibility, one type per file, pure rules + injected clock; the director rejects diffs that skip a layer.
