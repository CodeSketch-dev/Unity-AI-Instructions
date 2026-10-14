---
name: unity-fast-iteration
description: Shorten the Unity edit-compile-test loop: Enter Play Mode options, asmdefs, batched refresh, fewer reimports. Use when compile/Play is slow, MCP times out after script edits, or when setting up a project for fast iteration.
---

# Unity fast iteration

Each wait in the edit-compile-test loop is multiplied by dozens of iterations a day. Shave it where it is safe, and avoid triggering waits you do not need.

## Compile and reload time
- **Assembly definitions**: split into a runtime game asmdef, an editor-tools asmdef and (if present) framework glue; a change in one recompiles only its assembly and dependents. Keep third-party plugins in their own asmdefs/folders. Avoid circular references by layering (Core <- Logic <- Editor).
- **Batch edits, refresh once**: write all related script changes, then trigger a single refresh/compile and read the Console once. Every refresh costs a domain reload; per-edit refreshes multiply it. (Agents: do not call refresh after each file.)
- **Disable "recompile during play" surprises**: set script changes during Play Mode to recompile after exiting Play, so a stray edit does not drop the session.
- **Enter Play Mode Options** (Project Settings > Editor): disabling Domain Reload and/or Scene Reload makes Play start in a second or two. Cost: static fields and event subscriptions persist between runs. Only enable it once the project resets its statics (`[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` for caches, static buses, singletons) and keep a full-reload option for verification before milestones. Never claim a bug is fixed after a run with reload disabled until it passes with a full reload.
- Keep `Application.runInBackground = true` under `#if UNITY_EDITOR` so MCP/agent-driven sessions keep running when the Editor is unfocused.

## Import time
- Don't touch assets needlessly (reformatting `.meta`, re-saving scenes) because each triggers a reimport.
- Put big art in `_Art`/vendor folders that are not re-imported by script changes; keep texture/model import settings in presets so bulk imports don't need per-asset edits.
- Use the project's asset cache/accelerator if the team has one; keep the Library on a fast disk. Don't delete Library to "fix" a transient error; read the Console first.

## Shorter test paths
- A **test scene** or boot flag that jumps straight to gameplay with a seeded save; a **cheat menu** to set money, speed, zone, timeScale, reset save (`debug-cheats-menu`).
- Test one system in a small scene before running the whole game; keep a "sandbox" scene with the character, a ground and the system under test.
- Verify visual work with captured Game/Scene screenshots at reduced scale instead of long Play sessions.
- Run EditMode tests for pure logic (formulas, parsers, state machines): seconds, no Play Mode needed.

## For MCP/agent loops
- Keep each Editor call short and idempotent; long calls time out and are retried (`editor-tool-authoring`).
- After script edits wait for the domain reload to finish before the next call; poll the compile state rather than sleeping blindly.
- Read the Console through `unity-log-triage` or filtered to errors; never dump it whole.
- Don't enter Play Mode just to check compilation; compile status plus Console is enough, and Play Mode costs a reload.

## Measure
Time one full loop (edit -> compile -> Play -> reach the test state) before and after changes and record it in the project map's "Run it" section; keep a change only if the loop got shorter.
