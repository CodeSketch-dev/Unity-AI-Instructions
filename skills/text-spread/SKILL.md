---
name: text-spread
description: Use when creating Unity screen-space or world-space reward/stat text such as +money, +speed, +luck, or damage with a left TMP Sprite icon and right TextMeshPro label.
---

# Text Spread

Use this for the Knife Tower-style compact feedback item in either Canvas UI or world space: one pooled visual containing a left icon and a right TMP label, for example `<sprite name="money">+25`, `+12 Speed`, or `<sprite name="luck">+5 Luck`.

## Contract

- Use TextMeshPro/TMP Sprite Asset markup for the icon; do not create a separate Unity `Image` per spread item.
- Keep one shared icon atlas per project at **512×512 px**, divided into **16 fixed cells of 128×128 px**. Reserve stable cell IDs/names; never repack IDs casually.
- Create one TMP Sprite Asset from that atlas and use one material/preset compatible with the active TMP font material.
- Keep the runtime object pooled. Reset text, sprite asset, scale, color, alpha, position, tween state and parent on every reuse; release/unparent on completion.
- Icon is logically left and text is right. Prefer TMP inline sprite markup when baseline/kerning is acceptable; use a horizontal icon+label layout only when independent sizing or animation is required.

## Atlas and glyph setup

1. Author/import the 512×512 atlas with 4×4 cells. Keep transparent padding inside each 128×128 cell so the visible art, not its raw bounds, controls perceived size.
2. In the TMP Sprite Asset Sprite Glyph Table, select each glyph and tune `Scale`, `X/Y`, and glyph metrics to match the font cap height. Start at `Scale 1`; reduce oversized icons before changing the spread prefab.
3. Keep glyph rects aligned to the fixed cell (`X/Y`, `W/H` = 128) and use the glyph metrics/offset for fit. Do not resize the source atlas to solve one bad icon.
4. Name sprites semantically (`money`, `speed`, `luck`, `gem`, `star`) and validate that every referenced name exists before Play Mode.

## Text and layout defaults

| Item | Default |
|---|---|
| Text | TMP, no wrapping, overflow Overflow, middle baseline |
| Icon | TMP Sprite Glyph, white tint unless the reference requires tint |
| Icon visual height | about 60–80% of the label cap height; tune glyph `Scale` first |
| Gap | 4–10 px equivalent, then verify at target resolution |
| Label | compact number formatter; update only when value changes |
| Animation | pooled spawn, small scale-in/fade, upward drift, fade-out; use the project tween library |

For markup, use `<sprite name="money">+25` when the icon is part of the same text flow. If the icon must animate independently, use a `HorizontalLayoutGroup` with `LayoutElement` and a TMP label, while retaining the same atlas and glyph rules.

## Implementation and verification

- Resolve the current project's TMP version, font material, pooling API and tween library before writing code; do not invent a second pool or migrate DOTween/PrimeTween inside an existing subsystem.
- Add an editor validation/menu or import check that reports missing sprite names, duplicate semantic names, wrong atlas dimensions, and non-128 cell rects.
- Test at the smallest target aspect ratio and at a large font scale: icon must not overlap, clip, become unreadable, or change the label baseline.
- Verify pooled reuse over at least 20 consecutive spawns with no stale icon, alpha, transform, parent or tween state.
- A static/editor check is not proof of visual parity; capture a Play Mode screenshot when matching a reference game.

## Common mistakes

- Using a separate `Image` and many icon textures for every spread item: breaks the shared TMP atlas contract.
- Scaling the whole prefab because one glyph is too large: fix that glyph's Sprite Glyph Table `Scale`/offset.
- Recreating TMP Sprite Assets per prefab: use one shared atlas/asset and stable sprite names.
- Forgetting to clear the previous `<sprite>` markup on pool reuse: reset the full TMP text before assigning the next value.
- Using world-space coordinates for a screen-space spread without an explicit camera conversion.

## Size of spread texts
- Spread/pop numbers that fan out of a character (steps, XP, income) are small feedback, not headlines: keep them to roughly 4-6% of the screen height (about 45-65 px at 1080p) and let the animation, not the size, carry the emphasis. Keep ONE shared size constant for all modes (a style class) instead of per-prefab scales, and verify with a Play screenshot while the character is moving on the payout spot.
