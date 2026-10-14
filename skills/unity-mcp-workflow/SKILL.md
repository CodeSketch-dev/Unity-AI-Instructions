---
name: unity-mcp-workflow
description: Drive the Unity Editor through MCP safely: discover tools, inspect read-only first, edit prefab assets not scene overrides, batch, save, compile, read Console, screenshot, fallback. Use for any scene/prefab/asset/Play Mode/Console task.
---

# Unity MCP workflow

MCP is the only way to know the real Editor state. File edits do not prove that Unity compiled, imported, serialized or played anything.

## Session start
1. List the available Unity MCP tools and check connection status; prefer the team's default server (ivanmurzak) and do not mix servers for one operation. Never invent a tool name.
2. Confirm the Editor has the intended project and scene open (name/path) before touching anything.
3. Read the Console first to know the baseline errors.

## Stale-state guard
Before any MCP mutation or save of a scene/prefab, run `workspace_guard.py check` (skill `multi-agent-coexistence`): if the file changed on disk since you read it, reload it in the Editor first, otherwise the save overwrites the other agent's work.

## Operating pattern
1. **Inspect** (read-only): hierarchy, components, serialized values, assets, prefab status.
2. **Plan** the mutation; say what changes and what is preserved for broad scene/prefab edits.
3. **Mutate in small batches.** For prefab instances, edit the source prefab asset (open prefab, change, save), not a scene override, unless asked.
4. **Save**: scene/prefab/assets explicitly.
5. **Refresh + compile**, wait for domain reload to finish, then read the Console.
6. **Read back** the changed objects and verify serialized references (null, Missing).
7. **Play**: enter Play Mode, drive the feature, capture Console and a screenshot, exit Play Mode and ensure no scene changes were left from play.

## Tips and pitfalls
- Scripting-heavy edits trigger domain reload; wait for it before the next call or tools will time out.
- Large scene changes: prefer creating/editing prefabs and wiring in one place over many scene overrides.
- Object identity: use instance IDs/paths returned by the tool; names can be ambiguous.
- Do not hand-write Unity YAML or `.meta` files; ask the Editor to create assets.
- After transferring assets between projects, refresh the AssetDatabase and check import errors (`asset-transfer-closure`).
- Use screenshots (Game/Scene capture) to compare against reference images; attach them to reports.
- Keep an eye on selection/active-scene side effects of tools; restore what you changed.
- If another agent is editing the same project, coordinate (`multi-agent-coexistence`).

## Long and heavy operations
MCP calls that run too long time out **and are retried**, re-running your script. Keep each call short and idempotent, split big jobs into per-unit calls, write detailed results to a file, and follow `editor-tool-authoring` for generators. Check Editor state (not in Play Mode, not compiling) before each mutating call, and save after each stage. Web research via a browser tool needs that browser connected; if it is not, say so and ask instead of guessing references.

## When MCP is unavailable
Say exactly what failed (connection refused, wrong project, tools missing). Do only safe file-based work, mark everything as unverified in the report, and give the smallest next step (e.g. "reopen the Editor and check the MCP window shows Connected"). Do not repeatedly ask for reinstalls of tools that already work, and never claim Editor verification that did not happen.
