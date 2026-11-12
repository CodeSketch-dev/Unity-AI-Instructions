---
name: character-pack-skin-shop
description: "Turn a purchased character pack into a skin shop: catalog, importer, previews, unlock types, shop cards. Use when adding many skins from an asset pack with a shop and equip flow."
triggers: skin pack, character pack, skin shop, catalog, unlock, preview, thumbnail, equip, import pack
---

# Character pack to skin shop
1. Validate the pack with `character-skin-importer` (skeleton hash, budgets) and dedupe.
2. Register entries through `character-skin-system` and `config-and-factory-authoring`; bake thumbnails in the Editor.
3. Shop page: `shop-skin-preview` and `shop-tab-page-checklist`; price buttons per `price-button-contract`.
4. Unlock types (cash, gems, ad, free) are data; one equip event; saved via `data-block-template`.
5. Prove in Play: buy, equip, relaunch, still equipped.
