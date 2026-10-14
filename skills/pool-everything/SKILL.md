---
name: pool-everything
description: Pool anything spawned repeatedly (fx, floating text, projectiles, pickups) with PoolPrefabGlobal and PoolPrefabConfig, including adding a pooled fx. Use whenever code would Instantiate or Destroy in a gameplay loop.
---

# Pool everything spawned repeatedly

Use the framework pool: `PoolPrefabGlobal.Get/Release` with a `PoolPrefabConfig` asset (report 03, VERIFIED). Do NOT add another pool (`PoolPrefabShared`, `PrefabPooler`, ad-hoc `Stack<T>`, LeanPool) even though they exist in the reference code: they are legacy or counter-examples. SketchEngine ships the same API under `SketchEngine.Patterns.Pool`; read the installed `PoolPrefabGlobal.cs` before writing.

## Add a pooled fx / text / projectile
1. Prefab root carries `PoolPrefabItem` (missing = `LogError` at `Pool_Manager.Awake`, not at authoring time).
2. Asset `Configs/Pool/Pool_<Kind>_<Name>.asset` (Kind = Fx, Text, Bullet, Weapon): `_prefab`, `_persistAcrossScenes`, `_deactiveOnRelease` (true), `_poolPrewarm`, `_poolCapacity`, `_poolCapacityMax`. Prewarm <= max; size by spawn frequency. Defaults seen: hit fx persist, prewarm 25, capacity/max 50. Feature pools in subfolders.
3. `Factory_Pool` auto-collects the folder (`[AssetList(AutoPopulate=true)]`); `Pool_Manager` validates and calls `PoolPrefabGlobal.Init(configs)` once. If a project has no Pool_Manager, the factory's `OnInitialize` inits its own config.
4. Expose the config as a factory static or a serialized field; callers pass the config by reference, never by string id.
5. Spawn: `var fx = PoolPrefabGlobal.Get(cfg); fx.TransformCached.position = pos;` (typed: `Get<T>(cfg)`). Position AFTER `Get`.
6. Reset state in an `Init(...)` the spawner calls or in `OnEnable`; stop tweens in `OnDisable`. There is no central reset.
7. Release: `PoolPrefabGlobal.Release(cfg, gameObject)`; idempotent. `SetParent(null)` first. Never call it from a physics callback (package may `DestroyImmediate`; comment-level evidence). Pooled items release themselves on scene change.

## Instantiate is fine for
UI list items built once per screen, gacha/jackpot UI, skin swaps. Everything repeated in gameplay is pooled.

## Verify
Prefab has `PoolPrefabItem`; config in the auto-collected folder; no `Instantiate/Destroy` left in the loop; run `config-registry-audit` (see `config-and-factory-authoring`) for prewarm > max.
