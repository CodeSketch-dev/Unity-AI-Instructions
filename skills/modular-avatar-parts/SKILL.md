---
name: modular-avatar-parts
description: Modular avatar with slot parts (hair, hat, face, bag, tail) bound to a shared skeleton by bone name, preview-equip without saving, set items, pooled part prefabs. Use when the GDD has clothing/accessory customization instead of whole-character skins.
---

# Modular avatar parts

From steal-an-egg `CharacterSkin`, `AvatarPart`, `BoneMapper` (report 19 sec 1.4, VERIFIED; budgets INFERRED). Use when the Roblox game has hats/hair/clothes; whole-prefab skins (`character-skin-system`) suit "buy a character". Both can share one rig contract (`character-rig-and-animation-contract`).

- Slots: category x subcategory enums (reference: Avatar, Clothes, Accessories, Body x Items, Tail, Bag, Hair, SkinColor, Jewelery, Face, Hat). `Character_Part_Asset` per part: slot, prefab with a SkinnedMeshRenderer, baked bone-name list, price. A set item is a bundle of parts.
- Binding by NAME: the part prefab stores its root bone name, bone name list and saved bounds (`BoneMapper`); `TryLoad()` re-resolves bones under the character's skeleton and resets the renderer's local transform. Bake the mapping at import (`character-skin-importer`), resolve at runtime without `Find` (rig slots).
- Preview equip WITHOUT saving (shop try-on) and `SaveEquippedLook()` on purchase; unequip returns the part to the pool (`pool-everything`).
- Persistence: `Dictionary<slot, partId>` in `Data_Character` (ids only); event `Event_Character_Part_Equip(slot, asset, character)`.
- Visibility fades (the reference switches per-instance materials to Transparent at runtime): use a shared fade material or a property-driven dissolve on one shader instead (`one-material-world-shader` for the look, `character-rig-and-animation-contract` for the material rule).
- Budget: per-slot triangle caps inside the character budget (`character-perf-budgets`); parts share the character material atlas where possible.
- Ragdoll and die effects are siblings (shared pooled ragdoll prefab).

Verify: every part binds to the base skeleton, previews do not persist, buying persists, parts return to the pool, bones count stays within the rig limit.
