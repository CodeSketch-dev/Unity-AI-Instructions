# Parallelism model: one Editor, many hands (report 21 sec 3.4)

Hard fact: one Unity Editor == one project directory, and the Unity MCP controls that one Editor.

- **Editor lane (serial)**: everything that mutates scenes, prefabs, ScriptableObject assets, import settings, ProjectSettings, plus compile, Play Mode and screenshot tests. ONE builder agent (or the UI agent) owns it at a time and works a queue.
- **File lane (parallel, up to 4)**: C# code, EditMode tests, editor-tool scripts, CSV/config tables, GDD-derived data, docs, Python scripts. Run in subagents with worktree isolation (branch `gen/<task-id>`), no Unity open in the worktree. The producer merges worktrees into the main working tree between Editor tasks (rebase; never reset), then Unity compiles once for the batch.
- **Claims**: each task lists `claims` (`scene:`, `prefab:`, `asset:`, `code:`, `file:`); two tasks with an overlapping claim never run together (`orchestrator.py next` enforces it). Re-read a file immediately before editing; no whole-file rewrites; shared docs are append-only (`multi-agent-coexistence`).
- **Groups**: `G<phase>.<wave><letter>`: tasks of one phase at the same dependency depth with disjoint claims and at most one Editor-lane task. A group closes when every member is merged and one compile + Console read is clean. A group failure is bisected by task (discard that worktree), never `git reset`.
- Idempotent editor tools only (`rule-editor-tool-safety`): each generator removes its own previous output, caps loops, saves the scene after each stage, one stage per MCP call.
- More concurrency than 4 + 1 only raises merge cost and token burn.
