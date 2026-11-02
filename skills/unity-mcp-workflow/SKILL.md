---
name: unity-mcp-workflow
description: "Drive the Unity Editor through MCP safely: discover tools, inspect read-only first, edit prefab assets not scene overrides, batch, save, compile, read Console, screenshot, fallback. Use for any scene/prefab/asset/Play Mode/Console task."
---

# Unity MCP workflow

MCP is the only way to know the real Editor state. File edits do not prove that Unity compiled, imported, serialized or played anything.

## Session start
1. List the available Unity MCP tools and check connection status; prefer the team's default server (ivanmurzak) and do not mix servers for one operation. Never invent a tool name.
2. Confirm the Editor has the intended project and scene open (name/path) before touching anything.
3. Read the Console first to know the baseline errors. Record the latest sequence/timestamp and classify existing entries as baseline before any mutation; never clear the Console before preserving that baseline.

## Stale-state guard
Before any MCP mutation or save of a scene/prefab, run `workspace_guard.py check` (skill `multi-agent-coexistence`): if the file changed on disk since you read it, reload it in the Editor first, otherwise the save overwrites the other agent's work.

## CodeGraph boundary
When `.codegraph/` exists, use CodeGraph MCP first for C# source exploration and call-flow/impact questions. Treat its index as derived and potentially a few moments behind concurrent writes; it never replaces the stale-state check, one-writer coordination, or Unity MCP read-back. Use Unity MCP for the authoritative scene, prefab, serialized-reference, import, compile, Console, and Play Mode state.

## Operating pattern
1. **Inspect** (read-only): hierarchy, components, serialized values, assets, prefab status.
2. **Plan** the mutation; say what changes and what is preserved for broad scene/prefab edits.
3. **Mutate in small batches.** For prefab instances, edit the source prefab asset (open prefab, change, save), not a scene override, unless asked.
4. **Save**: scene/prefab/assets explicitly.
5. **Refresh + compile**, wait for domain reload to finish, then read the Console.
   Compare against the saved baseline: new compile errors are hard failures; pre-existing third-party/editor warnings stay visible as notes and are not silently treated as caused by the current task.
6. **Read back** the changed objects and verify serialized references (null, Missing).
7. **Play**: enter Play Mode, drive the feature, capture Console and a screenshot, exit Play Mode and ensure no scene changes were left from play.

## Tips and pitfalls
- Scripting-heavy edits trigger domain reload; wait for it before the next call or tools will time out.
- Large scene changes: prefer creating/editing prefabs and wiring in one place over many scene overrides.
- Object identity: use instance IDs/paths returned by the tool; names can be ambiguous.
- Do not hand-write Unity YAML or `.meta` files; ask the Editor to create assets.
- **Asset refresh precondition**: before any MCP `Refresh`, `AssetDatabase.Refresh`, asset import, generated-asset bake, prefab save, or scene save, inspect the Editor state and stop Play Mode first. Wait until `isPlaying == false` and compilation/import is idle, then perform the refresh. Never refresh or save project assets while Unity is playing; Play Mode changes can be lost or leave stale imports.
- After transferring assets between projects, stop Play Mode, refresh the AssetDatabase, and check import errors (`asset-transfer-closure`).
- Use screenshots (Game/Scene capture) to compare against reference images; attach them to reports.
- Keep an eye on selection/active-scene side effects of tools; restore what you changed.
- If another agent is editing the same project, coordinate (`multi-agent-coexistence`).

## Long and heavy operations
MCP calls that run too long time out **and are retried**, re-running your script. Keep each call short and idempotent, split big jobs into per-unit calls, write detailed results to a file, and follow `editor-tool-authoring` for generators. Check Editor state (not in Play Mode, not compiling) before each mutating call, and save after each stage. For asset refresh/import, the first mutation is always Stop Play Mode, followed by an idle-state check. Web research via a browser tool needs that browser connected; if it is not, say so and ask instead of guessing references.

## When MCP is unavailable
Say exactly what failed (connection refused, wrong project, tools missing). Do only safe file-based work, mark everything as unverified in the report, and give the smallest next step (e.g. "reopen the Editor and check the MCP window shows Connected"). Do not repeatedly ask for reinstalls of tools that already work, and never claim Editor verification that did not happen.

## Added from Unity official guidance (2026-11-02)
Source: official (Unity-Technologies/skills/unity-pipeline, unity-cli, project-auditor-fixes gotchas), our wording; applies to any tool that drives the Editor.
- Async operations (recompile, test runs, builds, audits) need polling: never assume completion from the trigger response.
- Recompile and tests can hang while the Editor is unfocused unless an editor tick/keep-alive is on; if a run stalls, check focus before retrying.
- Code reload of a method needs Play Mode; player-only commands need a development Player, not the Editor.
- When several Editors are open, target one instance or project path explicitly; confirm project name first.
- Script snippets run through an eval tool: fully qualify types and avoid extension methods and `using` lines when the tool compiles statements as a body; class-shaped snippets go through the execute-class form. Check the tool's own rules before writing long scripts.
- Code in a default `Assembly-CSharp-Editor` folder cannot reference types in asmdef assemblies: call them by reflection, or move the tool into an asmdef-aware Editor assembly.
- Play-mode timing and capture quirks (fixed screenshot size, retries after entering Play, reload before EditMode): see `playmode-driver-recipes`.

## Play Mode discipline (hang avoidance)
- Never edit scripts while Play is running: stop Play first, wait until `IsPlaying` is false (the stop call often still reports true for a few seconds), then edit and refresh. Compiling during Play hung the Editor twice.
- After any Play session `RequestScriptReload()` and wait ~45 s before EditMode; otherwise HUD layout tests fail on stale statics (not real regressions).
- The first Play after an Editor restart can take 60+ s and MCP calls fail with "after 10 retries": wait and retry, do not kill the Editor.
