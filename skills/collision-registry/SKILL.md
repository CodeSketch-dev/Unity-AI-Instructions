---
name: collision-registry
description: Route trigger and collision contacts through the framework OptCollisionRegister and OptCollisionSensor instead of per-object OnTrigger with GetComponent. Use when adding any pickup, platform, zone, checkpoint or hazard.
---

# Collision registry

Why: one physics callback owner (the moving actor) plus one dictionary read keyed by collider instance id replaces N callbacks and N `GetComponent` calls (cost model INFERRED, no profiler numbers exist, so never quote speedups).

## Shape
- Actor (e.g. `Character`) derives from `OptCollisionSensorFast<T>` and forwards: `OnTriggerEnterFunc(T t) => t.OnTriggerEnterFunc(this)` (same for collision enter/exit, trigger exit).
- World objects derive from `OptCollisionRegister` and implement the actor-family interface (`ICharacterCollidable`: four callbacks taking the actor). Keep bodies tiny; leave unused callbacks empty. One interface per actor family (`IEnemyCollidable`), never type-cast inside a callback.
- Registration happens in `OnEnable`, unregistration in `OnDisable`; colliders are gathered in `Awake`/`OnValidate`. Multi-collider objects register all of them.

## Pick the version first (`framework-version-map`)
| | older package form | SketchEngine (use this) |
|---|---|---|
| Base | `OptCollisionRegister<ICharacterCollidable>`; `Register2/3` for several interfaces | non-generic `OptCollisionRegister`; implement any interfaces |
| Match | typed map by T | sensor filters `owner is T` |
| Query helpers | `ForEach`, `GetSnapshot`, `TryGetFirst` | `TryFindFirst<T>`, `TryGetAll<T>` |
Both: use these helpers on overlap/raycast results instead of `GetComponent`.

## Failure checklist (VERIFIED in source)
1. Overriding `Awake/OnEnable/OnDisable` without `base.` = silently never (un)registered.
2. Colliders added at runtime are not registered; `_colliders` refreshes only in `OnValidate` outside Play.
3. Registry maps are static and framework never clears them: add a project `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` hook calling `OptCollisionLookup.Clear()` (domain-reload-off sessions leave stale entries).
4. v1 unregisters by re-reading `GetInstanceID()` of colliders; destroyed colliders leave stale ids (fixed in v2).
5. Sensor `T` must match the interface the world object registers under (v1 strict, v2 any implemented).

## Accepted exceptions (raw OnTrigger/OnCollision)
Pooled projectiles, actor-vs-actor contacts and one-off minigame trackers: a production project keeps a small set of raw callback files. Default; override when a profiler shows the registry is not the bottleneck.

Examples to read: a tiny register (kill plane), an overlapping-zones register with a static reset, and a detector implementing two collidable interfaces; see `house-code-patterns` references.
