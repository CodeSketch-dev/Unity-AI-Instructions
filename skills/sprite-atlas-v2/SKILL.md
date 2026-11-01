---
name: sprite-atlas-v2
description: "Sprite Atlas V2 setup: Sprite Packer mode, packables from Assets only, padding, prebuild generation, late-binding via Addressables. Use when UI or 2D sprites cause many draw calls, atlases are missing in builds or sprites show gaps."
triggers: sprite atlas, spriteatlas, atlas v2, sprite packer, draw calls ui, ui batching, atlas padding, tight packing, late binding atlas, addressables atlas, gop sprite, atlas giao dien, giam draw call ui
---

# Sprite Atlas V2

Source: official (Unity-Technologies/skills/manage-sprite-atlas), re-written; [ours] marks our additions.

## When
UI/sprite draw calls are high (Frame Debugger shows many batches from separate textures), a sprite is missing in a build, or tiles/sprites show seams.

## Facts
- Use Sprite Atlas V2 (Project Settings > Editor > Sprites > Sprite Atlas Mode). Enable Sprite Packer mode (Always Enabled, or Enabled For Builds) BEFORE creating atlases and read it back to confirm.
- Packables must come from the project `Assets` folder (folders or sprites). Built-in or package assets cannot be packed.
- In editor code do not script against the runtime `SpriteAtlas` except to read packables; use `SpriteAtlasImporter` / `SpriteAtlasAsset`. Never hand-edit .meta files.
- Padding at least 4 and Tight Packing off for tiles or filtered sprites; no mipmaps on UI atlases; keep compression consistent per atlas.
- Group sprites by screen/feature so a screen draws from one or two atlases. Do not mix always-loaded HUD and rarely seen popups in one huge atlas.
- Delivery: built-in (always needed UI) or late-binding through Addressables (optional content). Late-binding needs an Addressables build step AND a runtime loader bound to `SpriteAtlasManager.atlasRequested`.

## Steps
1. Inventory: sprite folders, current atlases, Frame Debugger batch count of one heavy screen (baseline).
2. Decide grouping and delivery; write the rule in the feature doc.
3. [ours] Prefer an idempotent Editor generator run from a build preprocess (`IPreprocessBuildWithReport`) over manual menu clicks so atlases never go stale; follow `editor-tool-authoring`.
4. Verify: Play, open the screen, Frame Debugger batch count after; no pink or missing sprite; build once and check atlas texture size in the Memory Profiler.

## Checks
Batch count before/after, atlas size under the platform max (2048 on low-end), no seams, Console clean. Report unmeasured items plainly.
