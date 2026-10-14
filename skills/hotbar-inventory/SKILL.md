---
name: hotbar-inventory
description: "Hotbar and inventory: Data_Inventory shape, static hotbar with selection event and slot fallback, scroll panel of owned tools, equip classes and locking rules. Use when adding a tool bar, backpack list or equipment slots."
---

# Hotbar and inventory

From thunder-break-egg `Egg_Hotbar` and knife-tower `Item_Inventory`, `Data_Item` (report 15 sec 5, VERIFIED). Pairs with `tool-weapon-pipeline`; UI pattern: `inventory` in `ui-pattern-library`.

## Data
`Data_Inventory : DataBlock` (`data-block-template`): `_tools Dictionary<string, Tool_Record {Owned, Level, Uses}>` (lazy `TryAdd`), `_equipped DataValue<string>`, `_hotbar List<string>` sized from the factory (slot -> tool id, "" = empty), `_selectedSlot DataValue<int>`, `_loadouts Dictionary<Equip_Slot, string>` for cosmetic slots (`cosmetic-slot-providers`), `_boosters Dictionary<string,int>` with caps. In `Init`: `base.Init()`, `??=` each field, CLAMP owned/equipped ids to the registry (as `Data_Egg.Init` does), grant the default free tool. Ids only: no scene objects or assets.

## Hotbar
- Static-state `Tool_Hotbar` with 5 slots (`enum` of kinds or ids), keyboard 1-5, `Select/CanSelect`, `EventChanged`; an empty slot falls back to slot 0; statics reset at `SubsystemRegistration` (TBE does, KT does not).
- Slot widgets and the held-model component react to `Event_Hotbar_Changed`; pets can map slots to pet ids.
- Two equip classes (KT): Battle (`Equipped`) vs Support (`EquippedBuff`, session-only, cleared in `Init`).

## Inventory panel
Scroll list built from the registry for owned entries into a ScrollRect content (`ui-scroll-board`), selection component per item, closes on player death; no per-frame text rebuild. Detail strip/panel, categories and sort are pattern variants.

## Locking rules
Free, per-life, per-session, permanent; `Lock()` re-equips the default if the equipped item becomes locked; events `Item_Locked/Unlocked/Equipped`.

## Missing in every reference (design if the GDD needs them)
Drag-and-drop reorder, stack counts for tools, durability. Pet bag capacity example: `ExtraSlotPrice(n) = 500 * 3^n` (TBE). No weapon-count cap exists.

Verify: equip survives restart, slot fallback works, owned list matches data, hotbar statics reset between Play sessions.
