---
name: unity-debugging
description: Systematic Unity debugging: reproduce, read first error, classify (null refs, prefab overrides, serialization, order, static state, events, raycast blocking, layers, timeScale, async) and fix the root cause. Use when something does nothing or errors.
---

# Unity debugging

Find the cause, then fix the cause. A null check that hides a missing reference converts a loud bug into a silent one.

## Procedure
1. **Reproduce** in the smallest scenario; note whether it happens in a fresh Play session, after scene reload, only on device, only after N minutes.
2. **Read the Console through `unity-log-triage`** (deduplicated summary; raw dumps waste context) and start from the top problem. The first error usually causes the rest. Note script, line and the exception type.
3. **Classify** using the table, then check the matching evidence.
4. **Form one hypothesis, test it** (log, inspector read-back via MCP, breakpoint-like prints, toggling a component). Change one thing at a time.
5. **Fix the root cause**, remove temporary logs, re-run the original scenario and the neighbors.
6. Record in `docs/qa/bugs.md` or the feedback notes if the cause was non-obvious.

## Failure classes and what to check
| Symptom | Likely cause | Check |
|---|---|---|
| Nothing happens on tap | UI raycast blocked / missing collider / no EventSystem | Raycast Targets, full-screen images, `_tapCollider`-style references, Graphic Raycaster, EventSystem present |
| NullReference in Awake/Start | unassigned serialized field, prefab override lost, execution order | inspect the *source prefab and the scene instance*; script execution order; initialization hooks |
| Works in scene, not in build | `Resources`/Addressables path, stripping, platform defines, editor-only code | IL2CPP stripping (link.xml), `#if UNITY_EDITOR` usage |
| Works first time, breaks after reload | static fields with domain reload off, singletons, event subscriptions | reset statics on `SubsystemRegistration`; unsubscribe in matching callback |
| Object invisible | layer/culling mask, scale 0 or negative, material/shader missing, behind camera far clip, fog | Frame Debugger, inspect transform and renderer, camera settings |
| Text mirrored or unreadable | negative scale, wrong facing, billboard rotation | transform scale sign, forward axis |
| Physics oddities | layer matrix, wrong collider type, trigger vs collision, autoSyncTransforms | collision matrix, `isTrigger`, Rigidbody on mover, interpolation |
| Stuck/lag spikes | GC alloc, per-frame find/LINQ, huge instantiate, loading on main thread | profiler timeline, allocation callstacks |
| Async code misbehaves after destroy | missing cancellation | owned cancellation token cancelled on disable/destroy |
| Old mesh/visual still shows after regenerating | stale GPU mesh from in-place asset overwrite, Static batching merged the old data | delete and recreate the mesh asset, reassign, un-Static the combined object |
| Edits vanished | made in Play Mode, or unsaved scene lost in an Editor hang/restart | check Editor state, save after each stage |
| Duplicates appear after running a tool | stale compile or MCP retry re-ran a non-idempotent script | make the tool idempotent (`editor-tool-authoring`) |
| Accelerated test finds nothing | gameplay timers are in game-seconds and expire at high timeScale | verify at 1x first (`unity-qa-playtest`) |
| Label floats too high | offsets stacked (parent extent + line offsets) | position relative to the real fitted bounds once |
| Animations snap | Animator toggling, root motion, ragdoll switch | sync pose before enabling physics, check Animator update mode |
| Works only on one aspect ratio | anchors/safe area | `mobile-hud-layout` test matrix |

## Principles
- Verify assumptions with tool output; do not guess which prefab/scene is active.
- Prefer fixing the data/wiring over adding defensive code; add defensive code only at true boundaries (loaded data, external input).
- Don't delete assets or scripts to silence errors.
- If it's another agent's work in progress, coordinate first (`multi-agent-coexistence`).
