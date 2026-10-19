---
name: character-rig-and-animation-contract
description: "Rule: one Character_Rig_Asset per skeleton family, fixed Animator parameter names, rig-owned controller, culling modes, no per-skin materials, slots by id. Use when adding a skin, rig, animation set or animator parameter."
---

# Rig and animation contract

Design from report 19 sec 3 (knife-tower facts VERIFIED, contract INFERRED). Why: skins from different sources only swap safely when skeleton, parameters and slots are a contract, not a convention.

## Rig
- One `Character_Rig_Asset` per skeleton family (humanoid, pet, ...): ordered required bone names, root bone, Generic or Humanoid flag, `SkeletonHash` (FNV-1a of the ordered names, `character-skin-importer/scripts/skin_validator.py`), the `RuntimeAnimatorController`, required parameters (name + type), slots `{id, bone, local offset}` (hat, hand_r, back/wing, tail, nametag), max bones (default <= 30; budgets in `character-perf-budgets`), local bounds.
- Generic with a shared bone-name skeleton is cheaper and keeps bone-name rebinding simple; Humanoid only when retargeting external mocap is required.
- A skin references the rig, not its own controller. When variants share a rig but need animation differences, use an `AnimatorOverrideController`.

## Animator parameters (fixed names, hashed once in a static class)
`Speed` or `VelocityZ` (float), `IsGrounded`, `IsJumping`, `IsJumpingDouble`, `IsClimbing` (bool), `ClimbY` (float), `IsSwimming` if used, `MotionType` (float), `HasWeapon`, `AttackType` / `TriggerAttack`, `EmoteId` (int) + `TriggerEmote`, `IsDead` / `TriggerHit`. Never rename per skin. Write parameters only if the controller has them (cache `animator.parameters` per animator into a `Dictionary<int, ParameterType>`, "IfExists" guards) so skins with a smaller controller do not warn (knife-tower `Character_Animator`).
Required clips (state names): Idle, Run (blend by Speed), Jump, Fall, Land, Climb, Dead/Hit, Win, optional Emote_01..N.

## Settings
Animator `CullingMode` CullCompletely for bots and far characters (the reference skin prefabs use 2), AlwaysAnimate for the player; update mode Normal; root motion off; display-only skins have no Animator.

## Forbidden
- `renderer.material` / `.materials` in `Awake` for every skin (climb-tower, steal-an-egg): per-instance copies break batching and leak. Use shared materials; create a runtime copy lazily for ONE character's effect and destroy it in `OnDestroy` (knife-tower stealth/freeze).
- `GetComponentInChildren<Animator>` lookups at runtime; refs are serialized and filled by the importer.
- Slot lookups by `Find`; resolve slot ids to transforms once at skin load (`Character_Slots`).
- Rigidbodies baked into every skin (`character-perf-budgets`).

Validate with `character-skin-importer`. Animator settings and controller assignment are checked statically (prefab YAML) and in the Editor.
