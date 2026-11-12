---
name: scene-teardown-safety
description: "Use when callbacks may arrive after a Unity owner is disabled, destroyed, or rebound, or when scene/mode transitions leave stale listeners, tweens, tasks or roots."
triggers: captured callback, stale callback, callback lifetime, unsubscribe, rebind, stale listener, callback cu, goi lai callback, huy dang ky
---

# Scene teardown safety

Bugs hide until you switch scenes/modes repeatedly: objects are destroyed in arbitrary order, so `OnDisable`/`OnDestroy` runs against already-destroyed neighbours.

## Rules
1. **Unity null check**: in `OnDisable`/`OnDestroy`/pool-return paths use `if (x == null) return;` (Unity-aware, not `?.` / `is null`) before touching any other component, pooled child or UI element. Guard at the owner that calls, not only at the callee.
2. **Skip work on unload**: gameplay cleanup (despawn, return to pool, spawn FX, post events) is skipped when the scene is unloading or the app quits (flag set in `OnApplicationQuit` / scene-unloading callback). Never `Instantiate`, pool-get or `StartCoroutine` from `OnDisable`/`OnDestroy`.
3. **Pool order**: pooled objects are returned before their pool root dies, or the pool ignores returns for destroyed items. Pool roots must not be `DontDestroyOnLoad` children that reference scene objects.
4. **DontDestroyOnLoad** roots (popup canvas, audio, EventSystem): exactly one instance; a new scene's duplicate destroys itself in `Awake`. Popups that survive a load are closed or reset in the scene-exit hook. Only root objects can be DDOL. Code after `base.Awake()` in a derived singleton still runs once in the doomed duplicate: guard with `Instance != this` (`persistent-root-prefab`).
5. **Duplicates**: one `EventSystem`, one `AudioListener`, one camera brain per loaded set. Singleton `Awake` handles a second instance.
6. **Lifetime pairing** (see `async-cancellation`, `static-bus-events`): every tween killed, task cancelled, bus listener removed in the matching callback; static collections reset on `SubsystemRegistration`.
7. **Invalidate callbacks as well as subscriptions**: unsubscribe prevents later event lookups, but does not invalidate a delegate already captured by a publisher or a callback already queued/in flight. Guard callback work against the receiver's current active lifetime. For replaceable bindings, capture a binding generation and the source identity; ignore calls when either is stale. Increment the generation before unbinding, including when rebinding the same source object.
8. **Prove stale calls are inert**: capture a callback, disable/unsubscribe, then invoke the captured delegate and assert no state changes. Repeat after rebinding to a different source and after rebinding to the same source; assert only the current binding updates state.
9. **Leave clean**: save data before leaving (`save-and-crash-safety`), restore `Time.timeScale = 1`, unmute/restore audio ducking, re-enable input, clear selected UI object.

## Repeatable scene-flow test (Play Mode, see `playmode-driver-recipes`)
Loop 5x: enter mode A -> play 3 s -> open and close a popup -> switch to mode B -> back. After each lap assert: Console has 0 new errors/warnings of type Missing/Destroyed/NullReference, `FindObjectsByType<EventSystem>()==1`, one AudioListener, `timeScale==1`, object count stable (no growth), no `(Clone)` leftovers outside pools.
Fix the cause (guard in the owner), not the test; a swallowed exception is not a fix.
