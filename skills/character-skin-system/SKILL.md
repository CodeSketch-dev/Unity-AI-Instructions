---
name: character-skin-system
description: "Character skin chain: Character_Skin_Asset, rig asset, Factory_Character, Data_Character, equip/unlock events, shared-mesh swap gated by skeleton hash, unlock types and per-mode type gating. Use when building the skin system or adding skins to a clone."
---

# Character skin system

Based on knife-tower / monkey-escape (VERIFIED) with the platform changes from report 19 sec 3 (INFERRED). Adding one skin: `recipe-add-skin-or-item`; validating it: `character-skin-importer`; rig rules: `character-rig-and-animation-contract`.

## Chain
- `Character_Skin_Asset : ScriptableObject` per skin under `Configs/Character/<Type>/`: ID = asset name (validated unique), localization key, `Character_Skin_Type`, rig, prefab, thumbnail/avatar sprites (baked by the importer), unlock type (Free / Gem / IAP none-consumable / IAP subscription / Ads / Daily) + price + IAP id, order, optional stat bonuses (e.g. speed bonus), read-only derived fields (UseSharedMesh, triangles, bones, materials).
- `Factory_Character` registry: default skin, arrays per type, dictionary by id built in `OnInitialize` with duplicate-id errors, `GetRandomSkin(type)`, allowed types per minigame, `GetEquipped()`, fallback (`config-and-factory-authoring`, `factory-singleton-template`).
- `Data_Character : DataBlock`: `Dictionary<string, CharacterSkinData{isUnlocked}>`, `DataValue<string> Equipped`, last normal equipped (`data-block-template`).
- Events: `Event_Character_Skin_Equip(asset, character)` (null character = player) and `Event_Character_Skin_Unlocked` (`static-bus-events`).

## Apply path (`Character_Renderer.LoadSkin`)
First load or different type -> instantiate the reference prefab from a pool keyed by skin id; same type + `UseSharedMesh` -> swap `sharedMesh` and `sharedMaterials` on the existing SkinnedMeshRenderer (no instantiate, no animator rebind). Shared swap is valid ONLY when the skeleton hash equals the rig's (the importer derives the flag; never hand-set it). Fire `EventSkinBeforeReleased` / `EventSkinLoaded`; animator, wings, tails, carpets and items re-bind on `EventSkinLoaded`. Mode gating: some modes force a default skin for restricted types (knife-tower forces Transformer/VIP to default in an event mode).

## Data pitfalls
- KT `SetEquipped` silently ignores an id never registered by touching `asset.Data`; always register on access and FAIL LOUDLY in the Editor for unknown ids.
- Free skins auto-unlock on first data read; subscription skins ignore the stored flag (live entitlement); expiry falls back to the default skin.
- Cached mesh/material fields that need an Editor "validate" button go stale silently: let the importer refresh them.
- Skin switchers (trigger zones that equip a skin) go through the collision registry (`collision-registry`).

## Unlock types
One enum + one entitlement rule per type; never grant before the purchase/ad callback (`unity-iap-port`, `ads-popup-flow`). Bots pick from allowed types (`bots-as-players`). Shop UI: `skin-shop` pattern and `shop-skin-preview`.

Verify in Play Mode: equip persists across restart, expired subscription falls back, swapping 10 skins allocates no new instances after warm-up, animator parameters survive the swap. Not Editor-verified here.
