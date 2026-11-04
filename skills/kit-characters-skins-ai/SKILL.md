---
name: kit-characters-skins-ai
description: "Use when building or porting the actor stack: one gameplay actor with swappable skin prefabs, skin assets/unlock/equip/shop, guarded animator contract, bot tiers and spawner, trails and burst FX, checkpoints/revive. Includes the skin-not-applying-in-another-mode regression lesson."
triggers: skin system, swappable skin, skin asset, equip skin, animator guard, animator parameters, bot spawner, bot tiers, trail provider, fx toggle, checkpoint revive, character kit, skin khong ap dung, doi skin, bot theo tier, knife tower style character
---

# Kit: characters, skins, AI, trails, checkpoints

Opt-in kit (see `prefab-kit-catalog`). Copy the shape, not the 1000-line actor file. Related: `character-skin-system`, `character-rig-and-animation-contract`, `bots-as-players`, `checkpoint-respawn`, `cosmetic-slot-providers`, `collision-registry`.

## 1. Architecture (right first time)
1. ONE gameplay/physics actor prefab (collision-sensor owner) serves player, bots and every mode; the art lives in a separate skin prefab loaded under an empty mount. Per-mode variants only for camera/UI (`minigame-consistency-contract`).
2. Skin variants are prefab variants that override only config + mesh + material; full rigs only for distinct monsters. Skin prefab carries animator, ragdoll, item container so "what it can wear" travels with the skin.
3. Same skin type + shared rig: swap `sharedMesh` + material on the existing renderer (no Instantiate). Different type: destroy + instantiate once.
4. Skin asset = ScriptableObject (id = asset name = SAVE KEY, never rename after release; type; thumbnail; unlock type Free/Ads/Gem/IAP/Subscription; price/product id). Subscription unlock is a live entitlement, never a persisted flag. Persist unlocked flags + equipped id in a `DataBlock`; `Get(id)` registers lazily (an unregistered id makes `SetEquipped` a silent no-op).
5. Equip contract: `Event_Skin_Equip(skin, actor = null)`; shop cells listen to equip/unlock events and ignore bots.
6. Instance materials created by stealth/freeze/tint effects are restored/destroyed in `OnDestroy` (colour-leak bug).
7. Bots never reload their skin on death (Destroy+Instantiate per death spikes frames).

## 2. LESSON: "skin does not apply in another minigame" (regressed 3 times)
Causes: (a) a broadcast with `actor == null` was matched with `actor.Is(...)` while another character class shared the same renderer component; (b) static "active mode" flags survived scene unload and filtered the event; (c) per-mode skin allow-lists (`SetAllowedSkinTypes`) not reset on mode enter.
Rules: match the local player via an interface property (`IsPlayer` on a shared event-source interface), never by concrete class; scope or reset every static mode flag (`RuntimeInitializeOnLoadMethod(SubsystemRegistration)` + reset in the mode master `Awake`); every mode that has its own character class must be in the equip test matrix. Test: equip skin A in mode 1, enter mode 2/3, assert the renderer loaded A; return and assert again (3 re-entries).

## 3. Animator guard
Static hash table; cache `animator.parameters` per animator and set only existing params of the right type; never Get/Set when `!isActiveAndEnabled`; push state through a per-tick diff-check; combine speed multipliers through named sources. This lets monsters/pets with partial controllers share one driver. Per-monster controllers expose only the params they need.

## 4. Bots by tier
`BotManager` prefab placed in the scene reads `{device tier -> {BotType: count}}` from the mode asset, spawns staggered (one per few seconds, cancel token), places on random waypoints, bot = actor variant with reduced controller options + `StateMachine<BotState>`. Bots share the player's progress index and teleport near it when far instead of simulating long routes. Count scales with `device-tier-policy`.

## 5. Trails and FX
`Trail_Provider` prefab holds disabled children keyed by trail asset; equip = deactivate old, activate new, `TrailRenderer.Clear()` + `ParticleSystem.Clear(true)` (no streak from the old position). Bursts (death, level-up) are pre-placed children toggled by `Fx_ToggleEmit`; global one-shots emit from ONE hidden instance per fx id. Additive unlit materials, lifetimes 0.5-3 s, maxParticles <= 200 (confetti excepted), no trail shadows.

## 6. Checkpoints
`ICheckpoint {Index, Transform}`; trigger registered in the collision registry posts `Event_Checkpoint_Enter`; only the player and `index > saved` saves; manager assigns indexes from hierarchy sibling order in an editor button; revive event teleports to the checkpoint and resets the camera. One interface with two sources (list manager / stacked tower) avoids coupling bots and revive to one layout.

## Done-check
Equip works in every mode scene (3 re-entries); save key stable; no GetComponent in contact callbacks; no allocation when swapping skins; bot count matches tier table; trail swap leaves no streak; Console empty.

## Pitfalls
Mixed tween libraries in one skin (pick one); animator params differing per controller; duplicated checkpoint classes (merge them); not covered by the reference: nametags, emotes, hat slot system, rarity table, preview camera.

References: [recipes](references/recipes.md), [images](references/images/README.md), [PROVENANCE](references/PROVENANCE.md).
