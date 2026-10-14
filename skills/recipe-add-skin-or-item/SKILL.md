---
name: recipe-add-skin-or-item
description: Add a character skin or item entry (asset, factory registration, unlock type, events, shop, save check). Use when adding purchasable or unlockable cosmetics or items.
---

# Recipe: add a skin or item

Traced from knife-tower `Character_Skin_Asset`, `Factory_Character`, `Data_Character`, `Shop_Skin` (report 03, VERIFIED; Brainrot shop visibility INFERRED). For a new rig or a modular avatar see the character skills (later task).

1. **Reference prefab** with a SkinnedMeshRenderer or MeshFilter + material. `_useSharedMesh=true` shares the existing skeleton; turn it off for a different skeleton.
2. **Asset** `Configs/Character/<Type>/Character_<Type>_<Name>.asset`: `_type`, `_skinName` (the ID key into the saved data, must be UNIQUE and never renamed after release), unlock type (`Currency_Type.Gem` + price; IAP none-consumable/subscription + product id via the IAP catalog dropdown; or daily-login-only), thumbnail/avatar sprites.
3. **Register** in the factory array for its type; `OnInitialize` fills the dictionary by ID. The reference overwrites duplicate ids silently: check uniqueness yourself (`config-registry-audit`). A brand-new type needs an enum value, dictionary push and shop edits (INFERRED).
4. **Persistence**: no code; `Data_Character.Get(ID)` creates the record lazily (`data-block-template`).
5. **Shop**: `Shop_Skin` lists the factory arrays, so registration makes it visible.
6. **Events**: unlock posts `Event_Character_Skin_Unlocked`; equip posts `Event_Character_Skin_Equip(skin, character)`; the switcher swaps the mesh (`static-bus-events`). An expired subscription falls back to the default skin.
7. **Verify**: no missing refs, listed in the shop, unlock -> equip -> mesh swaps, equipped skin survives restart, default fallback works. Do this in the Editor via Unity MCP before reporting done.

Items follow the same chain with `Item_Asset` (+ `[SerializeReference]` info) and `Factory_Item.Get(ID)`.
