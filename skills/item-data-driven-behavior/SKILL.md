---
name: item-data-driven-behavior
description: "Rule: item and tool behavior lives in the data class, not in switch statements, with no Instantiate for throws, no per-tick allocations, no try/catch around subscriptions, and cooldown cheats in factories. Use when reviewing or writing item, weapon or ability code."
---

# Item data-driven behavior

Anti-patterns found in the reference code (report 15 sec 1, VERIFIED in knife-tower) and the rule that replaces each:

| Smell | Rule |
|---|---|
| `switch (Item_Type)` choosing the throw/attack logic in `Character_Attack` | the polymorphic data class owns the algorithm: `[SerializeReference] Tool_Behavior` with `TryExecute` (`tool-weapon-pipeline`) |
| `Instantiate` (a create helper) for the banana throw | pooled projectile through `PoolPrefabGlobal` (`pool-everything`) |
| `new HashSet<Character>()` / `new List<Character>()` every 0.15 s in a tick | reusable buffers, cached collections (`combat-hit-detection-rule`) |
| `try { } catch { }` around event subscribe | symmetric subscribe/unsubscribe in `OnEnable`/`OnDisable` (`static-bus-events`) |
| cheat `InfinityHit` hard-coding a 0.6 s cooldown inside attack code | tuning and cheats come from the factory, one place (`factory-singleton-template`) |
| setters mutating a singleton asset at runtime | profile/override assets and layers (`kcc-character-controller`) |
| behavior chosen by enum ranges (1xx swords, 2xx throws) in code | the data decides: kind and behavior fields on the asset; enums only as ids |

Also: ids and records in `Data_Inventory`, never assets or scene objects (`hotbar-inventory`); every item has a held-visual entry in a provider dictionary, not an instantiate at equip. Review checklist for any item PR: no switch on type, no allocation in the hot path, no Instantiate/Destroy, tuning in config, events paired.
