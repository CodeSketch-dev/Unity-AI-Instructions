---
name: editor-lane-single-writer
description: "Rule: one Unity Editor is one project and one writer; only one agent mutates scenes, prefabs, assets and settings at a time, others work in file-lane worktrees. Use when dispatching parallel agents or when two agents might touch the same scene or prefab."
---

# Editor lane, single writer

Why: one Unity Editor instance controls one project directory and the Unity MCP drives that one Editor. The Editor can hold an older scene/prefab than disk and save over newer work; two agents entering Play Mode blocked compiles three times; two agents editing one builder collided (thunder-break-egg notes).

1. **Editor lane = serial.** Scenes, prefabs, ScriptableObject assets, import settings, ProjectSettings, compile, Play Mode and screenshot tests belong to ONE agent at a time (builder or UI agent). Queue the rest.
2. **File lane = parallel (max 4)**: C# code, EditMode tests, editor-tool scripts, tables, docs, Python, in worktrees with no Unity open.
3. **Claims**: every task lists claims (`scene:`, `prefab:`, `asset:`, `code:`); tasks with overlapping claims never run together (`orchestrator.py next`). Claim before editing, release after; respect other agents' claims (`multi-agent-coexistence`).
4. **Reload before saving**: after any external change (merge, another agent) reload the scene/prefab from disk before the Editor saves; re-read a file immediately before editing it; no whole-file rewrites from memory.
5. **Merge protocol**: the producer merges worktrees between Editor tasks (rebase, never reset), then one compile + Console read.
6. **Never fix another agent's compile errors** while it is working there: wait or report.
7. Idempotent generators only; one stage per MCP call; save after each stage (`rule-editor-tool-safety`).

Enforced by tooling where possible: the orchestrator lane limits, the PreToolUse protect hook and the claims check (plugin hooks, `hooks/`).
