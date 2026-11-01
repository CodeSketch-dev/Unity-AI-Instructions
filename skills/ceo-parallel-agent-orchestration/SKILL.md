---
name: ceo-parallel-agent-orchestration
description: "Run a studio-style loop: split work into file-owned pieces, launch parallel file-only agents, main agent owns Editor and verification, loop on feedback. Use when a request spans many independent pieces or a long autonomous session."
triggers: parallel agents, subagents, orchestration, ceo, backlog, file ownership, split work, dispatch, loop, nhieu agent
---

# Parallel agent orchestration
- Split into independent pieces with explicit file ownership; two writers never touch one file. Shared files get one owner.
- Agents do file/Blender/Python work only; the main agent owns the Editor: compile, Play, screenshots, tests (`editor-lane-single-writer`, `agent-team-protocol`).
- Briefs carry the performance budget, the docs to read first, and the report format. Logic-layer lane: pure C# in partial classes so agents do not collide.
- Verify every report yourself (compile, screenshot, numbers); send concrete feedback instead of accepting good enough.
- Keep a backlog file; start the next item when the previous passes review.
