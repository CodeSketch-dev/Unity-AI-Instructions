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
