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

## Edit mode must equal Play (owner standing rule, binding for every agent, automatic)
- Every UI frame, board, popup, HUD, shop and billboard is a real prefab (or scene object) authored in Edit mode and looks EXACTLY as in Play. Runtime only fills data (pet names, icons, numbers, prices). Never build UI frames at runtime, never leave test/builder output in a scene.
- Junk UI is a defect: it bloats the build and cannot be hand-edited. After ANY UI or builder work run this sweep in Edit mode and delete (after proving unused: the real prefab is referenced elsewhere, e.g. in the feature's Factory asset) everything it reports, then save the scene:
  `foreach Transform t in FindObjectsByType<Transform>(Include): if t.name.EndsWith("(Clone)") && t.gameObject.scene.IsValid() -> report/DestroyImmediate` (plus any `PrefabUtility.IsAddedGameObjectOverride` object under a UI prefab instance that no code references).
- The Game view in Edit mode must show the same screen as Play at the same moment (HUD, popups closed). If a board, placeholder text (Trail, Rarity, Lorem, New Text) or foreign-game art (Knife Tower clones) is visible in Edit mode, it is a bug: fix the prefab, not the runtime.
- When a layout or UI is redesigned, update the prefab and its builder so Edit mode and the builder output both equal the final Play look; a builder that is run again must reproduce it (idempotent).

- Bakers must reference ASSET sprites: a sprite generated at runtime (procedural rounded rect, Texture2D created in code) is not serialized into the baked prefab and silently becomes null (plain rectangle in Play). Load kit sprites with AssetDatabase.LoadAssetAtPath and verify the baked prefab in Play.
- One loading look across scenes: keep the loader alive (DontDestroyOnLoad) through scene activation and fade it after the first frames of the new scene; never fade out before activation (the old scene canvas flashes).
