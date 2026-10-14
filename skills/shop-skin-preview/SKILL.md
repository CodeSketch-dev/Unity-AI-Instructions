---
name: shop-skin-preview
description: "Skin shop preview: default baked thumbnails, optional live 3D stage with own layer, camera, RenderTexture, light and drag-rotate, pooled lifecycle and stale-load token. Use when a shop must show characters, pets or weapons."
---

# Shop skin preview

Default (knife-tower, climb-tower, problox): a baked thumbnail sprite in an `Image`; the pattern is `skin-shop` in `ui-pattern-library` (selection event, action button per unlock type). Choose live 3D only when the GDD needs rotate-to-inspect or an animated preview. The only 3D precedent mined is knife-tower's trail preview (Kamgam `WorldImage`, skin spawned at (10000, 0, 0)); drag-rotate was not found in game code, so the stage below is a design (INFERRED; template `assets/PreviewStageDrag.cs.txt`, UNCOMPILED).

## Baked thumbnails
Render a transparent 256x256 PNG per skin from the preview stage in the importer (`character-skin-importer`), assign `Thumbnail` and `Avatar`. Locked items: black silhouette via ONE shared flat material, not a property block per renderer. Zero runtime cost.

## Live stage (`Character_Preview_Stage` prefab)
- Placement far from play space, own layer `UI_Preview` excluded from the main camera mask and gameplay lights.
- One dedicated camera: perspective FOV 25-30 (WorldImage's default 60 is too wide for characters), culling mask `UI_Preview` only, SolidColor alpha 0, HDR off, MSAA off, no post volume; disabled when the popup is closed.
- Output `RenderTexture` 512x512 (256 on low tier), ARGB32, depth 16, no mipmaps/MSAA, shown in a `RawImage`; release it in `OnDisable`/`OnDestroy`.
- One directional light with the preview culling mask, no shadows; optional rim light on the high tier only.
- Skin from the pool at the stage origin, Idle animation, `AlwaysAnimate` while visible, effects disabled; swap through the same `LoadSkin` path as the game.
- Drag-rotate: pointer-drag handler on the RawImage rotating the stage pivot `rotationY += delta.x * 0.4`, inertia damping 6, snap back after 2 s; handle drag only on that rect so the item ScrollRect still scrolls.
- Lifecycle: `Event_Shop_Skin_Item_Selected` -> `Show(asset)`; hide -> release skin to the pool and disable the camera; a version token drops stale async loads (problox `_loadVersion`).

Budgets: one RT, camera on only while visible, zero per-frame allocation (`character-perf-budgets`). Verify: select 20 items quickly (no stale model), close the popup (camera off, RT released), drag does not scroll the list. Not Editor-verified.
