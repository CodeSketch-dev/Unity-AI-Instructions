---
name: cosmetic-slot-providers
description: Equippable cosmetic slots (aura, trail, wing, pet) with asset SO, data block, equip event and a provider that toggles pre-baked visuals; pet follow tick. Use when adding auras, trails, wings or pets to the character.
---

# Cosmetic slot providers

From knife-tower and monkey-escape (report 04 sec 9, VERIFIED). Skins/items entries: `recipe-add-skin-or-item`; pets as a system: `pet-system` (not yet written).

## Pattern
- `Aura_Asset` / `Trail_Asset` / `Wing_Asset` ScriptableObjects: multiplier (aura/trail 1.5 on XP/speed gain; wing jump multiplier 2, additive on the jump layer), price (IAP, daily login, currency), prefab, thumbnail.
- `Data_<Slot>`: unlocked set + equipped name; `Event_Character_<Slot>_Equip` on change (`static-bus-events`).
- `<Slot>_Provider` on the character skin holds `Dictionary<Asset, GameObject>` of PRE-BAKED visuals; equipping toggles active objects and clears TrailRenderers/particles; nothing is instantiated at equip time (`pool-everything` for anything else).
- Skins reload fires an "equipped visuals" refresh (children re-attach on `EventSkinLoaded` / `EventSkinBeforeReleased`).
- Wing: a zone posts `Event_Wing_Equip/Unequip`; `Character_Wing` adds/subtracts the jump vertical multiplier layer (never the base value); some skin types exclude wings.
- Bots: random aura/trail changed every N revives (reference N = 20).
- Pet follow (reference): registry ticked from one manager (HashSet + remove buffer, try/catch per pet), straight-line seek move speed 3, rotate 240 deg/s, arrive 0.1 m; use a ring-buffer follow for several pets (`pet-follow-equip-evolve` design).

Verify: equip persists across restart, multiplier applies once, unequip restores base values, no GC per frame from the tick.
