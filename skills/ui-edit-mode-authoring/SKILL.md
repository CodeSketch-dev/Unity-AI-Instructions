---
name: ui-edit-mode-authoring
description: "Use when changing UI art, texture, sprite, frame, size or layout of a popup, HUD, shop, toast or button: bake the final art/size/text into the source prefab in Edit Mode; runtime only shows/hides and fills data. Never old placeholder art swapped at runtime."
triggers: ui art, new texture, sprite, restyle, thay art, art moi, texture moi, prefab, runtime, edit mode, placeholder, old popup, popup cu, 9 slice, set size
---

# UI: author in Edit Mode, runtime only shows

Owner rule (standing, every project): when a UI gets new art/texture/frame, the NEW art goes straight into the source prefab. There is no "temporary old art, then code overwrites sprite/size at runtime".

## Rules
- The source prefab is final when opened in Edit Mode: final sprites, Image type (Sliced/Simple) and border, sizes, anchors, fonts, texts/layout, colours. What you see in Prefab Mode is what the player sees.
- Runtime code may only: show/hide (SetActive/alpha/animation), fill data, play feedback. Data-driven content is FREE at runtime: item/skin/pet/food icons, names, counts, prices, rarity colours, list entries from config. It must NOT set sprites/frames/materials of STATIC art (frames, backgrounds, buttons, headers, tabs), resize rects, restyle fonts, call a "builder"/"apply style" at Awake/OnEnable, or Resources.Load static UI art to replace what the prefab holds. Test: if the picture is the same for every item/state it belongs in the prefab; if it depends on data it may be set at runtime (its slot, size and frame stay authored in the prefab).
- Default state is hidden or empty-but-valid: never ship placeholder text ('Text', 'New Text', 'Label', sample names/rarities) or default sprites (UISprite, Knob, Background) in a prefab.
- Use Editor builders/menu tools (idempotent) to produce or patch prefabs, then save the prefab. A builder is an authoring tool, never a runtime dependency. After saving, re-read values back from the asset.
- Replacing a UI means deleting the old one in the same change (prefab, scripts, builder, registry entry, tests, sprites no longer referenced). Prove unused by GUID/path/class scans first (`tech-debt`); old popups left in the project are dead weight and show up as 'ghost' UI.

## Check before reporting done
1. Open each changed prefab in Edit Mode (not Play): screenshot/inspect; art, size, text are already final.
2. Grep the feature's scripts for `.sprite =`, `sizeDelta =`, `Resources.Load`, `ApplyStyle`, builders called from runtime: none touches static art.
3. Audit rules: PLACEHOLDER-TEXT and RUNTIME-RESTYLE (default texts/sprites in prefabs; runtime art swaps) report 0 over `Assets/_Game`.
4. First frame in Play equals the final look (no flash of old art).
