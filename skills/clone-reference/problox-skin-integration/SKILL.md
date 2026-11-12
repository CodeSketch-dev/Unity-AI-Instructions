---
name: problox-skin-integration
description: "Use when putting the problox engine character skin (Problox_Character_Skin, CharacterSkin, AvatarPart sets) on a KCC character in another game: scale, safe API, animator and bones."
triggers: problox, skin, character skin, avatar part, engine skin, ragdollcontroller, animator moi, 8 huong
---

# Problox engine skin on a game character

- Instantiate `Problox_Character_Skin.prefab` under the character's `Graphical/SkinRoot` once (serialized prefab ref, no Resources.Load). Engine avatar is ~4.04 tall: scale SkinRoot 0.42 for a 1.7 m capsule (too big -> camera inside body -> occlusion-fade colours everything flat cyan).
- Safe API: `EquipShopItem(set)`, `LoadSkinRandomMix(0.5f,0f)`, `UnequipAll`. NEVER call `LoadSkin()`, `SaveEquippedLook()`, `IsSetOwned` (need GameSaveData) or `PlayerDieBreak.Break/Revive` (need CharacterManager). Equip uses the engine pool (PoolManager creates itself lazily).
- Engine controller `Base_Character` only has Idle/Run/Jump (IsRunning/IsJumping/IsSprinting), no blend tree: author OUR OWN controller and clips (Run_Reverse = time-reversed Run asset; Animator.speed<0 is not allowed at runtime) and keep model/rig/skin from the engine.
- 8-direction feet when players face the partner: pure sector/hip-yaw maths with hysteresis (EditMode tested), hips yaw within +-90, spine counter-twist, runs in LateUpdate after the Animator.
- Ragdoll: engine `RagdollController` (standalone), not our own runtime builder; restore turns bone colliders off again.
- Write animator params only on change; hysteresis on run, short debounce on airborne.
