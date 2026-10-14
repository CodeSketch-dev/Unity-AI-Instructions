---
name: recipe-add-pickup
description: Add a collectible (coin, gem, boost) with registry collision, data write, sfx, respawn and prefab. Use when a GDD or request adds a new pickup type.
---

# Recipe: add a pickup

Traced from knife-tower `Collect`, `Collect_Gem` (report 03, VERIFIED). Detect the framework version first (`framework-version-map`); collision base differs (`collision-registry`).

1. **Script** `Scripts/Logic/Collect/Collect_<Name>.cs`: `: Collect` (a register + `ICharacterCollidable` base with empty callbacks). Serialized `_value`, `_respawnTimeInSeconds`. Override `OnTriggerEnterFunc(Character c)`: call `base`, guard `if (!c.IsPlayer) return;`.
2. **Collect-once memory** (only if needed): add a keyed accessor to the matching `Data_X` (lazy `TryAdd`, see `data-block-template`) and a scene-instance GUID field generated in `OnValidate` (skip prefab assets and prefab stage), plus a `[Button] GenerateGUID`.
3. **Effect**: `Data_Currency.<X>.Value += value` (the DataValue change drives the HUD); sfx through `AudioManager.Play(Factory_Audio.<Sfx>)` (new `AudioConfig` in `Configs/Audio/` and a field in `Factory_Audio`); a notification text via the project helper.
4. **Collision wiring**: nothing manual; the base registers child colliders in `OnEnable`. Prefab = root with the script, child collider `isTrigger` on a layer the actor reaches (check the layer matrix), mesh/vfx child. Save under `Prefabs/Collect/`, place instances in the scene.
5. **Respawn**: `SetActive(false)` then a PrimeTween delay to re-enable; stop the tween in `OnDestroy`; check `this == null` in the callback.
6. **Fx**: use a pooled fx via `pool-everything`, never `Instantiate`.
7. **Verify** (Unity MCP, not file edits): compiles, no console errors, collect as player changes value and HUD, restart shows persistence, respawn works, non-player does not collect.

Soft defaults from the reference; override when the project's pickups differ.
