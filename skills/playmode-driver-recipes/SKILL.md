---
name: playmode-driver-recipes
description: "Headless-ish Play Mode testing through script-execute when no game-view screenshot or input tool exists: ScreenCapture, real UI taps via EventSystem raycast, input driver, GameView aspect, save backup, blocking popups. Use when verifying UI or gameplay by Play Mode."
---

# Play Mode driver recipes

Extends `playmode-script-testing` (reflection checks). Use these when you need real taps, real screenshots and character movement. Run under the Editor lock (`agent-team-protocol`).

1. **Clear blocking popups FIRST** (mandatory): full-screen offline / idle-income / free-reward popups cover the HUD and ruin screenshots and taps. After every Play start and every load, tap the claim/close control with a real tap (below) and re-check before any other step.
2. **Screenshot**: `UnityEngine.ScreenCapture.CaptureScreenshot(path)` inside script-execute; the file is written next frame, so return and read it in the NEXT call. Use a scratch folder outside `Assets/`.
3. **Real UI tap**: build a `PointerEventData` (position in screen px, **origin bottom-left**), `EventSystem.current.RaycastAll`, take the first hit, then `ExecuteEvents.Execute` pointerDown, pointerUp, pointerClick on it. Avoids `onClick.Invoke` blind spots (blocked raycasts, wrong layer, open animation ignoring Close).
4. **Drive a character**: an `EditorApplication.update` driver feeds the project's player-input component (move vector, jump) toward a target; remove the callback when done and on domain reload. One driver at a time.
5. **Aspect ratios**: set the Game View size via reflection on `UnityEditor.GameView` (set the selected size index / custom size) to test 9:16, 9:19.5 and 3:4 for UI.
6. **Focus**: Play freezes when the Editor loses focus; set `Application.runInBackground = true` at runtime only (script or `#if UNITY_EDITOR` bootstrap). Never commit a ProjectSettings change made for testing.
7. **Saves**: before the run copy the save file and record its md5; after the run restore and compare. Reset test-changed data (money, timers) and reflected config.
8. **Scene hygiene**: Play-created objects are `(Clone)`; never save a scene while in Play Mode or with leftovers. After Stop, grep the scene file for `(Clone)` and check `git diff --stat` shows only intended scene changes.
9. **Time**: stretch timers by config/reflection, restore `timeScale`, one action per call when a frame matters.

Report numbers and screenshot paths; state what only a device can verify.
- Tutorial gating can hide HUD buttons (alpha 0, no raycast): taps report "no hit" until it is complete or skipped.
- Polling a result file written by a test runner (e.g. `Temp/test_results.txt` that says `running` then `done pass=N fail=M`): the file from the PREVIOUS run still says `done` until the new run rewrites it, so a poll started too early reports a stale result. Check the file mtime or wait until it has been seen as `running` once; re-arm a Monitor before it expires, since a full PlayMode suite can take ~17 min. A UI test run also leaves the Game View at the test's size: reset it afterwards.
- Spawn/teleport spots in "never fall through the ground" tests must avoid dig pits and other holes: the legitimate floor there is lower and can move with the clock, so assert against the ground measured under the player (excluding its own collider), not a fixed y.

## Gotchas (MCP capture and timing)
- The MCP game-view screenshot tool renders at its own fixed size (e.g. 2160x1080); resizing the Game View does not change it, so portrait cannot be captured that way. Use an in-script capture at the wanted size instead.
- Compositing a canvas into a RenderTexture under URP can return a blank frame; prefer `ScreenCapture` for overlay canvases.
- `script-execute` right after entering Play can fail with "Failed to invoke ... after 10 retries" until the domain finishes loading: wait a few seconds and retry.
- EditMode tests run after a Play session need `EditorUtility.RequestScriptReload()` first (statics survive with domain reload off).
- Opening a modal that needs progression (rebirth, premium shop) for a screenshot: in Play, read the save's private data via reflection, remember the original values, set the minimum (gear mask, cash), invoke the HUD's private press handler, capture, then WRITE THE ORIGINALS BACK before leaving Play. A daily/welcome modal may cover the target: deactivate it by name first. The modal screenshot can land mid fade-in (translucent): judge layout, not colour.
- Game View size: pick the entry by WIDTH>HEIGHT inside the group of the CURRENT build target (`GameViewSizes.currentGroupType`, e.g. Android), never an index taken from the Standalone group. A wrong index gave 1080x2160 / 720x1280 portrait on a landscape game. Verify `Screen.width > Screen.height` before every capture.
- Offline / welcome popups re-open every time the Editor regains focus in Play; claim them with a UI click right before each capture and again after a long wait.
- Long QA runs: write results to a file from an EditorApplication.update driver (timeScale up to 4-8, restored in a finally) and wait on the file with Monitor, never with sleep chains.

- Testing offline/return flows in the Editor: with domain reload off the save object and its "boot evaluation done" cache survive Play exits, and a script reload resets any clock override you set. Instead, rewrite the persisted last-seen timestamp in the save on disk (or via the data API) while stopped, then enter Play once.

- A static clock delegate set before entering Play is reset by [RuntimeInitializeOnLoadMethod] static resets on Play start: an Editor-only persisted offset (EditorPrefs / ScriptableSingleton read by the clock) is the reliable way to fake elapsed time across a Play boot.

## Shared Editor guard
- Before a Play test that calls a discard-unsaved-scene-changes helper, check `git status` / the other session progress file mtime: another agent may hold unsaved scene edits in the same Editor, and the discard deletes them. Wait until it commits or is idle, or save its scene first.

## Fresh-player run: prove the save was really clean (trap)
- Deleting the save files and entering Play in the same call right after a previous Play stopped can leave the old state (the stopping session rewrites its save, or the game reads cached data). Sequence: stop Play, wait until not playing, delete files + PlayerPrefs, THEN enter Play.
- Before trusting the run, check the first screen is the first-time flow (tutorial, no returning-player popups such as daily login). Returning-player values (same reward amounts as the real save) mean the run is NOT fresh: discard it.
- Always keep the backup/restore pair (copy persistent folder aside, restore after) and restore even when the run is discarded.

## Do not log a defect from one capture right after an action (trap)
- Damped systems (label overlap nudges, fly-ins, popup pops, count-ups) settle in 0.3-1 s. A frame captured the instant after a click can show a transient overlap that is gone later. Before writing a defect row: wait ~2-3 s, capture again, and only log what persists; note "transient" otherwise.
- Check the system's own resolver exists first (e.g. a stack/declutter pass) and whether its size estimates match the real text width, instead of assuming it is missing.

## New HUD widget gate check
A widget gated like a sibling (e.g. hidden until FTUE ends) can stay inactive in a returning-player Play run; force-activating it with SetActive does not show it if a parent is stashed. Before committing a new HUD chip, find which gate hides it and capture it visible (or say "not seen in Play"); EditMode layout tests alone do not prove it renders.
