---
name: scene-teardown-safety
description: "Prevent teardown-order bugs when switching scenes or modes: destroyed pooled objects in OnDisable, surviving popup roots, leaked tweens/tasks/listeners, duplicate singletons. Use when adding scene or mode switching, pools, or after a MissingReferenceException on exit."
---

# Scene teardown safety

Bugs hide until you switch scenes/modes repeatedly: objects are destroyed in arbitrary order, so `OnDisable`/`OnDestroy` runs against already-destroyed neighbours.

## Rules
1. **Unity null check**: in `OnDisable`/`OnDestroy`/pool-return paths use `if (x == null) return;` (Unity-aware, not `?.` / `is null`) before touching any other component, pooled child or UI element. Guard at the owner that calls, not only at the callee.
2. **Skip work on unload**: gameplay cleanup (despawn, return to pool, spawn FX, post events) is skipped when the scene is unloading or the app quits (flag set in `OnApplicationQuit` / scene-unloading callback). Never `Instantiate`, pool-get or `StartCoroutine` from `OnDisable`/`OnDestroy`.
3. **Pool order**: pooled objects are returned before their pool root dies, or the pool ignores returns for destroyed items. Pool roots must not be `DontDestroyOnLoad` children that reference scene objects.
4. **DontDestroyOnLoad** roots (popup canvas, audio, EventSystem): exactly one instance; a new scene's duplicate destroys itself in `Awake`. Popups that survive a load are closed or reset in the scene-exit hook. Only root objects can be DDOL.
5. **Duplicates**: one `EventSystem`, one `AudioListener`, one camera brain per loaded set. Singleton `Awake` handles a second instance.
6. **Lifetime pairing** (see `async-cancellation`, `static-bus-events`): every tween killed, task cancelled, bus listener removed in the matching callback; static collections reset on `SubsystemRegistration`.
7. **Leave clean**: save data before leaving (`save-and-crash-safety`), restore `Time.timeScale = 1`, unmute/restore audio ducking, re-enable input, clear selected UI object.

## Repeatable scene-flow test (Play Mode, see `playmode-driver-recipes`)
Loop 5x: enter mode A -> play 3 s -> open and close a popup -> switch to mode B -> back. After each lap assert: Console has 0 new errors/warnings of type Missing/Destroyed/NullReference, `FindObjectsByType<EventSystem>()==1`, one AudioListener, `timeScale==1`, object count stable (no growth), no `(Clone)` leftovers outside pools.
Fix the cause (guard in the owner), not the test; a swallowed exception is not a fix.
