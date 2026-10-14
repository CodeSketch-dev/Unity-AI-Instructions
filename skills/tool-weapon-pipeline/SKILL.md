---
name: tool-weapon-pipeline
description: "Data-driven tool and weapon system: Tool_Asset with polymorphic behavior, Tool_User state machine with impact timing, shared player/bot entry, held visuals, cooldown HUD, three worked examples. Use when adding pickaxes, swords, guns or any held tool."
---

# Tool / weapon pipeline

Synthesis of knife-tower (`Item_Asset` + `[SerializeReference] Item_Info`), thunder-break-egg (pickaxe swing at normalized clip time) and climb-tower (bombs, pickaxes) in report 15 (VERIFIED code facts; the generic design and HP numbers are INFERRED). House style and file layout: `config-and-factory-authoring`, `factory-singleton-template`, `data-block-template`.

## Data
- `Tool_Asset : ScriptableObject`: id, name, `Tool_Kind` (Melee, Mine, Ranged, Thrown, Support), rarity, icon, held prefab, `Tool_Stats` struct (Damage, Cooldown, Range, ConeHalfAngle, ImpactNormalized 0..1, SwingSpeed, Knockback, CritChance, CritMultiplier, MoveSpeedMultiplier, MaxTargets), `[SerializeReference] Tool_Behavior`, upgrade block, audio/fx refs, purchase info, tier.
- `Tool_Behavior` abstract with subclasses `Melee {cone, layer}`, `Mine {node tag}`, `Projectile {pool config, speed 50, lifetime 4, pierce}`, `Thrown {arc, fuse, blast radius, falloff}` exposing `bool TryExecute(Tool_Context)`: the DATA class owns the algorithm (the reference's `switch (Item_Type)` in attack code is the anti-pattern, `item-data-driven-behavior`).
- Persistence: `Data_Inventory` records ids only (`hotbar-inventory`). `Factory_Tool` builds dictionaries in `OnInitialize`, validates duplicates.

## Runtime
- `Tool_User : MonoCachedHub<Actor>` owns `StateMachine<Tool_State>` (Idle, Windup, Impact, Cooldown) (`state-machine-template`). `TryUse()` is the ONE entry for player input and bots (`bot-brain-waypoints`).
- Windup triggers the swing animation at `SwingSpeed` and schedules impact at `clipLength / speed * ImpactNormalized` (TBE 0.88; KT fixed 0.25 s after press, fx at +0.1 s) with a tween/UniTask delay, cancelled on unequip/death (`async-cancellation`). Impact calls `behavior.TryExecute`, which uses the allocation-free resolver (`combat-hit-detection-rule`) and applies `DamageInfo` (`combat-health-status`).
- Cooldown state fills the HUD attack button; cooldown cheats live in the factory, not inline.
- `Tool_Held` swaps PRE-BAKED held models/fx on `Event_Tool_Equipped` (provider dictionary, `cosmetic-slot-providers`); stat layers (move-speed, jump multipliers) are added on equip and removed on release.
- Events: `Event_Tool_Equipped/Unequipped/Used/Upgraded`, `Event_Hotbar_Changed` (`static-bus-events`).

## Flow of one use
Input -> `TryUse` -> Windup (anim) -> delay to impact -> resolver finds targets -> `ApplyDamage` -> `Event_Combat_Hit` drives floating text, hit fx, haptic, shake (`game-feel-polish` `references/combat-feel.md`) -> kill -> loot roll (`loot-rarity-tables`) -> currency fly (`currency-spread-fx`) -> Cooldown.

## Worked examples
`references/worked-examples.md`: pickaxe (mine, 15 tiers), great sword (melee cone), bomb (thrown AoE). Reference numbers are soft defaults; HP-based player damage has no reference and must be tuned with the balance loop.

## Wiring checklist
Factory singleton asset exists and is assigned; tool assets under `Configs/Tool/`; held prefabs and pool configs; `Tool_User`, health and target components on the ACTOR SOURCE PREFAB (not a scene override); attack button, cooldown image, hotbar slots; attackable layer mask and collision matrix; compile, Console clean, EditMode tests for the pure formulas, Play Mode test equip -> swing -> hit -> kill -> loot -> save/load (`done-means-wired`). Not Editor-verified in this repo.
