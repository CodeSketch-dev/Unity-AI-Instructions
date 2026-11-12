# Detailed loading-screen contract

## Scope and evidence

Use this reference when implementing or repairing a studio splash, startup artwork, scene loader or initialization task queue. Its acceptance criteria are engineering requirements, not a claim that an arbitrary project already passed them. Inspect the installed source and Editor state before selecting concrete class names or APIs.

**Design objective:** give the player a readable, authored loading presentation while prerequisites and permitted ads finish, then enter a ready game once. Preserve existing saves, SDK integration and scene architecture.

**Implementation plan:** inspect entry flow -> classify tasks/gates -> wire serialized presentation -> implement UniTask orchestration -> compile -> exercise the timeline and failure paths -> measure UI/native on device. Reuse an existing loader when it can satisfy the contract; extend it rather than maintain two transition owners.

## Ownership and view

- Put the controller and view in authored scene/prefab objects. Serialize the studio root/logo, game root/art, progress fill/text, native slot and optional fade group. Keep them editable in the Hierarchy/Prefab Mode.
- The controller owns phase changes, cancellation, task registry, ad requests and scene operation. The view only presents progress and measures its authored slot; it must not start loads or ads independently.
- Either the boot scene owns the whole startup, or a persistent overlay survives activation. Record which. A boot-owned controller is destroyed by a Single-mode scene switch, so it cannot await target-scene postactivation work without transferring ownership first.
- Keep one EventSystem and one appropriate AudioListener across the loaded scene set. Persistent manager scenes are an optional existing architecture, not a reason to duplicate every manager.
- Check assembly dependencies: a runtime assembly must not reference default-assembly SDK scripts. Put the narrow bridge in a permitted dependency direction; do not reach internal save types across assemblies.

## Phase and timing contract

| Phase | Required behavior | Exit gate |
| --- | --- | --- |
| Studio | Logo visible at intended aspect; input blocked; initialize existing services after the first rendered frame where practical | Configured unscaled minimum and any explicit studio prerequisite |
| Game loading | Artwork covers without distortion; progress readable; native occupies its reserved region if ready | Minimum display time plus all preactivation tasks |
| Fullscreen opportunity | Hide native first; show app-open only when allowed and ready | Not shown, failed, or close callback completed |
| Scene staging | Load asynchronously; keep activation disabled | Scene reaches its ready threshold and all prior gates remain satisfied |
| Activation/finalization | Activate once; keep overlay if target-scene tasks remain | Target scene initialization completes; display 100% and release input |

Expose phase durations as serialized tuning. Two seconds of studio logo followed by five seconds of game loading is an example, not a global ad requirement. An alternative ad phase order is valid when specified and verified. Do not quietly change the user's chosen order.

Measure minima from the moment the relevant view is presented. Real work may take longer. Prefer `Time.realtimeSinceStartupAsDouble` for wall-clock minima across the first rendered frame, or an equivalent monotonic UniTask realtime delay. `Time.unscaledTime` can jump across Editor startup/frame initialization: verify measured wall durations instead of trusting the configured delay. Loading must also work at timeScale zero. Never label a timed bar as actual disk/scene progress.

## Extensible UniTask tasks

Offer a registration shape equivalent to:

```csharp
void RegisterLoadTask(Func<IProgress<float>, CancellationToken, UniTask> task);
UniTask LoadAsync(string sceneName, CancellationToken cancellationToken);
```

Use the installed framework's cancellation wrapper or a linked token source. Pass tokens through delays, frame yields, asset work and task implementations. Observe fire-and-forget exceptions using the project's convention. Never run Unity API work via `Task.Run`.

Define registration boundaries explicitly:

- **Preactivation:** registered by the boot scene or persistent services before execution starts. Examples: existing save warmup, config registry preparation, safe pool warmup or asset downloads that do not require target scene objects. These tasks can gate target activation.
- **Postactivation:** registered by target scene `Awake`/`Start`. Examples: target scene mesh combining or component initialization. They can gate hiding the overlay and unlocking input, but cannot gate their own scene's initial activation.
- Give a postactivation registry a deterministic collection window or explicit registration-complete signal. Do not guess that an arbitrary one-frame delay captures all async registrants.
- Freeze or drain each queue under a documented policy. Reject late work after the phase closes; never silently leave it for the next load. Clear queues after completion/failure and on static reset.
- Treat required task exceptions as failed prerequisites: record task identity and keep the failed target inactive. Clear ownership/busy state and provide the project's retry/fallback path. Do not catch and report success.

Run tasks sequentially when ordering matters. Only parallelize independently owned work; one task failure must cancel or observe its siblings. Allocate progress adapters once per task rather than every frame. Prefer synchronous main-thread `IProgress<float>` reporting; `System.Progress<T>` dispatch can delay UI updates.

Weight scene load, required tasks and minimum-duration presentation separately. Clamp task reports to 0..1 and keep displayed progress monotonic. Smooth display toward the target, but do not wait forever for an `Update`-driven smoothing animation if its object is disabled. Set final display to 100% explicitly after actual completion.

## Scene activation and interruption

1. Validate the requested scene/path/build entry before changing presentation or requesting ads.
2. Acquire the common busy gate before the first await. Include externally started scene operations under the same owner.
3. Render the loading view before expensive work. Avoid a frame of gameplay before the overlay exists.
4. Set `allowSceneActivation = false` immediately after starting the scene operation. Unity staging progress commonly stops at 0.9; normalize by that threshold. Never await `isDone` while activation remains false.
5. Complete all preactivation gates, then permit activation once. Target-scene `Awake` is the instrumented proof of this boundary.
6. If target work registers after activation, retain a persistent overlay/input gate until it finishes. Enter playable state only after this second boundary.
7. Hide the overlay/fade in only after the correct ready gate. Avoid a fade to an empty old scene immediately before a long activation stall.

Unity cannot cancel a started scene operation. Leaving it at 0.9 may block later async scene operations. Prefer running cancellable prerequisites before starting staging when early preload offers little benefit. If staging can outlive its owner, document and implement the interruption policy: transfer the operation to a surviving owner, or safely finish it and recover. Releasing activation merely to unblock the queue is an interrupted recovery path, never a successful loading result. Test it separately from normal activation ordering.

## Existing ads, saved state and callback handling

- Keep the functioning provider/network and existing request configuration. Loading UI is not authorization to add a mediation network or rewrite working load/show code.
- Initialize existing save bindings/migrations before reading ad flags; do not construct an expensive full gameplay facade solely to inspect one entitlement if a safe existing accessor exists.
- Honor saved remove-ads, applicable timed ad-free entitlements, consent and platform policy before requesting native or app-open. Do not turn a saved refusal into consent. A new consent mechanism is a separate product requirement.
- Verify provider installation order: a temporary Editor/mock provider can report readiness before the real SDK bridge's `Awake` replaces it. Wait for the real provider's lifecycle rather than infer readiness from an unrelated initialized flag.
- Use the loading duration as a bounded inventory opportunity. No inventory/offline skips that ad. Do not create an unbounded startup SDK wait.
- Once a real fullscreen ad opens, await its close/failure callback before activation. Resolve completion once even if SDK/facade both report failure. An arbitrary timer must never enter gameplay under a still-visible ad.
- Distinguish a callback that never arrives from an ad still open. Any watchdog must reconcile the provider's actual fullscreen state and lifecycle; report telemetry rather than blindly advancing.
- Launch app-open has one owner. Resume logic must recognize an ad-induced pause and the last fullscreen close time, preventing another app-open immediately after the first.
- Hide native before fullscreen, activation, owner teardown and failure recovery. Match banner restoration to the existing global banner service instead of creating a loader-local banner loop.

## Native slot and presentation

Measure a dedicated RectTransform after layout under the real Canvas/camera. Obtain all four corners, convert to screen pixels, intersect with the safe area and reject an invalid/tiny result. Keep progress, status text and any close affordance outside that region; native views are composited above Unity UI.

Convert pixels to the SDK's documented logical units. For an SDK scale expressed in pixels per logical unit:

```text
x = pixelRect.xMin / deviceScale
y = (screenHeight - pixelRect.yMax) / deviceScale
width = pixelRect.width / deviceScale
height = pixelRect.height / deviceScale
```

Use the SDK/device logical scale and inspect the native provider's actual template sizing API. Physical `Screen.dpi` is not Android logical display density. A correct request rectangle alone does not prove the chosen native template rendered at that size; measure the returned/native device rectangle too. See `native-ad-beside-popup` for the provider sizing contract.

Handle safe-area/resolution/orientation changes by recomputing or hiding the native. Poll readiness at a modest interval or use existing readiness events; no per-frame allocations. Hide/reload through the existing SDK ownership rules.

Art: original studio identity, readable silhouette, adequate contrast and transparent export where needed. Game loading art should match the game's actual art direction. Use an EnvelopeParent/cover strategy for background artwork; preserve logo aspect with a bounded rect. Do not bake progress text into art. Run required UI fitting/outline/layout/ink audits and inspect screenshots; measure every touched container.

## Cleanup and direct scene Play

Use `finally` for owned native cleanup, transient audio restoration, queue clearing and busy release. Cancel tasks when the owner is disabled/destroyed or replaced; dispose owned sources and remove paired subscriptions. Do not persist temporary loading mute values to the player's sound preferences.

Reset launch flags, static registries and busy state on `SubsystemRegistration`. Avoid duplicate startup screens when entering the game from the new boot path. Direct Editor Play from a gameplay scene must remain usable according to the existing project convention; it must not accidentally replay the full production ad startup every test.

If the project already loads a persistent manager scene additively, keep that arrangement: initialize it once, load content through the same entry point, bracket unload/load with fades and avoid duplicate manager stacks. This portable pattern was adapted from the Apache-2.0 Unity open-project-1 example; its coroutine/event plumbing is not an implementation requirement.

## Required validation ledger

Back up the save before Play and restore afterward. Record actual evidence, not an expected timeline copied from configuration:

| Scenario | Assertions/evidence |
| --- | --- |
| Normal build entry | Studio/game first-visible times and minima; tasks complete; native show/hide; app-open close; target Awake; overlay hidden; input enabled |
| No inventory/offline | Startup finishes without ads; duration bounded; target activates once |
| Explicit refusal/remove-ads | Zero ad show attempts; saved flags unchanged |
| Slow preactivation task | Target Awake absent until task completion; progress <100% before completion |
| Target postactivation task | Target can awaken, but overlay/input gate remains until task completion |
| Required task throws | Failure recorded with identity; no false success/target activation; busy cleared; retry/recovery usable |
| Duplicate load request | One scene operation and one ad opportunity; no duplicate task execution |
| Owner disabled/destroyed | Work cancelled; native gone; no abandoned queued operation or leaked callbacks |
| App-open close/failure | Callback resolves once; activation after closure; ad-induced resume does not show a second ad |
| Restart/reload | Static reset with domain reload off; no stale tasks or duplicate managers/listeners |
| Five scene-flow laps | One EventSystem/AudioListener; stable object count, timeScale/audio/input restored; clean Console |
| Three target aspect ratios | Play screenshots looked at; layout/ink totals, dx/dy, text containment; native requested vs actual bounds |

Compile and inspect source-prefab references through the correct Unity MCP. Run relevant EditMode/runtime assertions and report PASS/FAIL/SKIP counts. Editor mocks can prove ordering and no-inventory behavior; they cannot prove real native sizing, real app-open callbacks or low-end device performance. Mark those checks unverified until device evidence exists.
