---
name: scene-flow-loading
description: "Build gated Unity splash and loading flows. Use when startup needs a studio logo, game artwork, progress, async tasks, app-open/native ads, or delayed scene activation."
triggers: loading screen, splash screen, studio logo, startup flow, loading tasks, scene activation, app open loading, man loading, man hinh tai, thanh loading, logo studio, tai scene, splash
---

# Splash, loading and scene activation

Use the existing loader before introducing another. Read [the detailed contract](references/loading-screen.md) for implementation or a startup defect. This skill owns transition orchestration; `boot-sequence-setup` owns framework initialization order; `persistent-root-prefab` owns the object that hosts the loaders. Studio standard: scenes are loaded in Single mode only (no additive scenes, no streaming) through TWO loaders that live in the persistent root: a heavy loading screen (progress, task queue) and a light fade transition loader. Contract of both: [two-loaders.md](references/two-loaders.md).

## 1. Inspect and record the contract
1. Verify the connected Editor project, build scene order, actual entry component, installed UniTask/framework, SDK provider, save flags and existing loader callers. Read a requested reference through its own MCP; label source-only observations accordingly.
2. Record the phases, minimum durations, ad opportunity, task registration lifetime, activation point and ownership in the task plan. A studio 2 s + game artwork 5 s sequence is one configurable product choice, never a universal default.
3. Split tasks into **before activation** and **after activation**. A target scene's `Awake` cannot register work before that scene activates. Move such prerequisites into the boot/persistent owner or keep the overlay while postactivation tasks finish.

## 2. Implement one transition owner
1. Use one shared busy gate for synchronous entry points, UniTask APIs, fades and externally started loads. Set it before awaiting; clear it in `finally`. Reject duplicate requests.
2. Use scene-authored prefabs and serialized view references (`scene-authored-prefabs`); load `ui-always` before changing their UI. Separate studio logo, game art, progress and reserved native slot. Never runtime-build the loading hierarchy.
3. Expose cancellable task registration with progress, for example `Func<IProgress<float>, CancellationToken, UniTask>`. Register before the owner's task window closes; clear completed/stale registrations and reset static state on `SubsystemRegistration`.
4. Render the overlay before heavy work. Use unscaled UniTask timing and monotonic progress; reserve 100% for completed gates, never for elapsed time alone.
5. Validate the scene before loading. Stage `LoadSceneAsync` with `allowSceneActivation = false`, normalize its loading progress by 0.9, then enable activation only when all preactivation gates finish. Keep the overlay/input blocker until postactivation tasks also finish.
6. Guard cancellation, task failure, missing scenes, duplicate instances and scene teardown. Unity scene operations cannot be cancelled: follow the explicit interruption policy in the reference instead of abandoning an operation at 0.9.

## 3. Integrate existing ads safely
1. Preserve the installed mediation/provider. Do not add another network just to obtain a loading flow. Read saved consent, remove-ads and applicable active entitlements before any ad attempt; retain explicit refusals.
2. Treat ad readiness as a bounded opportunity during loading. No inventory skips the ad; it never traps startup. A shown app-open holds activation until its close/failure callback resolves exactly once. Never timeout an actively visible ad into gameplay.
3. Measure the authored native slot after layout; convert screen pixels to the provider's actual logical units using SDK device scale, never physical `Screen.dpi`. Keep native clear of progress/text and hide it before fullscreen ads or exit. Apply `native-ad-beside-popup` for SDK sizing details.
4. Own launch app-open in one place. Suppress legacy launch overlays; prevent resume logic from showing another fullscreen ad after the launch ad closes. Clean up native and temporary audio ducking on every exit.

## 4. Verify before reporting
- [ ] Compile; inspect serialized references, missing scripts and Console through Unity MCP.
- [ ] Play from build scene 0 with a backed-up/restored save; record studio/game phase durations, task completion, app-open close, activation and overlay-hidden timestamps.
- [ ] Assert target scene `Awake` occurs after every preactivation gate; assert controls unlock only after required postactivation tasks finish.
- [ ] Exercise no inventory, saved refusal/remove-ads, duplicate request, task failure, cancellation, direct scene Play and domain-reload-off restart. Repeat scene transitions per `scene-teardown-safety`.
- [ ] Run layout/ink audits and inspect Play screenshots at project aspect ratios: report counts, dx/dy, text bounds and native slot/requested/actual rectangles.
- [ ] Verify real native/fullscreen callbacks on device; Editor mock readiness is not device evidence. Report measured total loading time and any unverified Android behavior.

## Behavioural routing checks
- "Logo 2 seconds, then art/native 5 seconds; wait before entering the game" -> load this skill plus UI/ads skills; inspect real entry scene and prove activation ordering.
- "Add a loading task that reports progress" -> classify pre/postactivation, pass cancellation and verify failure/reentry cleanup.
- "Scene opens behind the bar while app-open is showing" -> inspect activation gate and duplicate launch/resume ownership before editing.
- "Only change the gameplay enemy's damage" -> do not route here; select gameplay/combat skills.
