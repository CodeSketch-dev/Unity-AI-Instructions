---
name: tmp-sprite-icons
description: "One shared TextMeshPro Sprite Asset for inline icons (cash, gem, power, egg, star) used by world TextMeshPro text via sprite tags, built by an Editor baker, with a pure string helper. Use when text must carry a currency/stat icon in 3D or world-space labels."
triggers: tmp sprite, sprite asset, inline icon, sprite name, floating text icon, world text icon, tmp icon
---

# Shared TMP sprite icons

- Build ONCE: an Editor baker packs the icon sprites (blit non-readable sources through a RenderTexture) into one 512 px atlas PNG (sRGB, no mips, bilinear), creates the TMP_SpriteAsset next to it in a Resources folder, glyph advance = width, bearingY ~0.85 x height so the icon sits on the baseline, faceInfo pointSize ~150. Idempotent, no dialogs, returns a status string.
- Link it as a FALLBACK of the project default sprite asset (and the default as fallback of the new one) so old and new tag names both resolve. Re-running an older icon builder can drop the link: re-run the baker.
- Runtime helper (pure strings, unit-tested): Tag(name), WithIcon(name, text) (idempotent, unknown name gives plain text), Apply(TMP_Text) assigns the asset once at label creation. Rebuild the string only when the value changes (no per-frame concat).
- UI uses Image + TextMeshProUGUI in a HorizontalLayoutGroup instead; sprite tags are for world TextMeshPro. See ui-icon-text-everywhere.
- Verify: Play probe with a 3D TextMeshPro using every tag; icons must sit on the baseline at the real label size.
