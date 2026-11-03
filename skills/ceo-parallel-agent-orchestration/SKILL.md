---
name: ceo-parallel-agent-orchestration
description: "Run a studio-style loop: split work into file-owned pieces, launch parallel file-only agents, main agent owns Editor and verification, loop on feedback. Use when a request spans many independent pieces or a long autonomous session."
triggers: ai-agent-hub, codex agents, orchestrator, parallel agents, subagents, orchestration, ceo, backlog, file ownership, split work, dispatch, loop, nhieu agent
---

# Parallel agent orchestration
- Split into independent pieces with explicit file ownership; two writers never touch one file. Shared files get one owner.
- Agents do file/Blender/Python work only; the main agent owns the Editor: compile, Play, screenshots, tests (`editor-lane-single-writer`, `agent-team-protocol`).
- Briefs carry the performance budget, the docs to read first, and the report format. Logic-layer lane: pure C# in partial classes so agents do not collide.
- Verify every report yourself (compile, screenshot, numbers); send concrete feedback instead of accepting good enough.
- Keep a backlog file; start the next item when the previous passes review.

## Orchestrator mode with ai-agent-hub (Codex / Claude / Gemini workers)
- The main agent is the ORCHESTRATOR: it plans, splits, dispatches, reviews strictly and verifies in the Editor; code-writing, research and Blender work go to workers.
- Hub MCP (`mcp__ai-agent-hub__*`, load via ToolSearch "ai-agent-hub"): `list_accounts` first (ids are integers; `max_concurrency` 1 = one task per account at a time), then `create_task` (title, instructions, provider `codex`, `account_id`), then `submit_parallel_tasks` with `task_ids` (array of ids from create_task), then poll `get_task_status` / `get_task_result` / `get_execution_logs`. `list_workers` / `list_projects` may be empty: workers start on submit, project is optional. If tools return empty after a hub rebuild the session holds the old binary: ask the user to reconnect the MCP or restart Claude.
- Instructions must be self-contained: absolute project path, language and house style, FILE OWNERSHIP (files the task may touch and must not), no git, no .unity/.prefab/.meta edits, what to report. Workers cannot run Unity: they re-read edited files and call sites; the orchestrator compiles and Play-tests.
- Never accept a report without `git diff` of the touched files, a compile with an empty Console and a Play check of the feature; send concrete corrections back as a new task. A task call that errors or is "interrupted" may still have edited files: check `git status` before retrying.
- Art (icons, concept images, sprites) goes through the `codex-game-art` MCP (`generate_game_image`, short single-image calls; long tasks time out), 3D through Blender scripts; verify results visually before using them.
- Unity stays single-writer: only the orchestrator (or one named agent) enters Play, refreshes assets or saves scenes at a time.
