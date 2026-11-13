---
name: ui-text-tmp
description: "Use when creating or rebaking TextMeshPro font assets, creating labels or titles, or diagnosing text fit, line spacing, font metrics, outline, or optical centring. Part of the ui-always set."
triggers: TMP, TextMeshPro, font rebake, rebake font, TTF, OTF, SDF metrics, FaceInfo, font line spacing, font baseline, tao font, font chu
---

# UI text (TMP)

Facts from the studio evidence notes (KT 451 TMPs, VERIFIED); defaults, not law.

- **NEVER a dark, grey or navy text face (owner order 2026-11-12, always on)**: every label, title, number and toast keeps the shared WHITE (light) face with the dark outline, on dark AND light boards, like the reference game. Never fix legibility by darkening or greying the face (reads as dim/dead text); use the outline/underlay of the shared material or a darker plate behind. Audit: grep UI prefabs for TMP `m_fontColor` that is not white/approved = defect.
- **Outline via material presets**, not the Outline component: a bold display font with outline widths ~0.35/0.75/1.0 and a heavier font 15-50, white face, black outline/underlay. World-space text uses the instancing/billboard variant.
- **Autosize on** (about 80% of labels): min 18 almost always, max by role (36-52 common, 72 titles). Use no-wrap and Center/Middle alignment ~88%; do not use Overflow to hide a label that does not fit. Vertical centring: see Optical centring below; set it once in the text factory, never a per-label nudge.
- **Raycast Target off** on non-interactive TMPs (82%) and decorative Images.
- **Color**: white face everywhere (87%); accents only for state words: gold F4C046, orange FFA800, yellow F3F300, gray 909090, red FF2C00, green 48FF00. Image tint stays white (97%): color lives in the sprite.
- Dark ink on light panels only for names; coloured outlined text for rarity/state.
- **Numbers**: compact K/M/B via the project `BigNumber` over `DataValue<double>`; set text only when the value changes; count-up tween 0.7 s OutCubic unscaled (`ui-feedback-toasts`).
- Fonts: one display font plus per-locale fonts (`ui-localization`).
- Long names: autosize, never wrap into the neighbouring control. TMP inset about 10 px per side inside its box (`ui-design-tokens`).

## Rebaking a TMP SDF font from source outlines

Use this only when a TMP SDF asset is being regenerated from a TTF/OTF or another outline source.

1. Treat the outline file as glyph outlines, not a backup of the TMP asset's SDF `FaceInfo`. When the original TMP asset exists, capture and compare its complete `FaceInfo` field set and glyph/atlas generation settings before rebaking.
2. Keep the intended glyph set, atlas sampling/resolution and padding consistent with the source asset. Record the generated sampling `pointSize`; do not tune atlas padding or glyph sampling to correct line spacing.
3. Compare every `FaceInfo` field. Set `pointSize` to the generated sampling size and scale only unit-bearing metrics by `generatedPointSize / sourcePointSize`; preserve dimensionless values. Do not copy metrics from a different font or locale font.
4. Validate the actual wrapped text at the same text, width and size as the reference. Compare line count and adjacent line baselines after layout settles, then inspect a Play screenshot for matching line advance, clipping and overlap.
5. If the original SDF metrics are unavailable, record them as unknown and validate against a native rendered reference; do not claim the outline file preserved them.

## Optical centring (label looks high or low)

Cause: button/header sprites are 9-sliced with a thicker bottom lip, so the visible face centre sits above the RectTransform centre, and TMP Middle/Midline centres on font metrics, not cap height. Seen in a reference project: titles about 5 units low, labels with a fixed +5 up to 3 high.

- **Target**: cap-height centre of the text = face centre of the nearest Sliced Image ancestor = rect centre + (border.bottom - border.top) / 2 / (sprite ppu / 100 x pixelsPerUnitMultiplier). Symmetric sprite = 0. Cap centre = baseline + `font.faceInfo.capLine` x font scale / 2.
- **New UI**: set vertical alignment to **Capline** once in the text factory/builder. Measured in Unity: Capline puts the cap centre exactly on the rect centre for any size and string; Middle sits about 0.033 x fontSize high; Geometry/Midline vary with the string. Then the y offset is only the face offset above (0 on symmetric plates). No hand "+5" per label.
- **Existing prefabs**: run `assets/Qa_TextCenter.cs.txt` (copy to Editor/Qa; menu Tools/QA/Center Text dry, then apply). Idempotent. It measures under a temp Canvas (TMP bounds are invalid off-canvas) and edits via `LoadPrefabContents`. It skips multi-line text, layout-group children, non-middle alignment, faces taller than 260, labels far from the face centre, shifts over 7, and plain symmetric frames over 3.5.
- **World text** (3D TextMeshPro, world canvas, nameplates, floating labels): same Capline rule, so the anchor is the visual centre of the caps; put it on the plate/icon centre and add the face offset only over a sliced plate (scale the offset by the label's lossy scale). `Qa_TextCenter` covers UGUI prefabs only; check world text by screenshot at gameplay distance.
- **Verify**: Play, open the popup, screenshot; label centre within about 1 px of the face. Restart Play Mode first: popups created before the edit keep the old layout.
- Leave third-party UI sets alone (different atlases/ppu, measured deltas unreliable).

Default from a reference project; override when the project's own reference shows otherwise.

## Fit contract

Put every label inside its owner’s padded content area, not directly against a button, Board or Frame border. Resolve TMP preferred bounds after layout: at the configured minimum font, text must remain inside its inset and must not cover another content/control sibling. A button may grow for its preferred icon+label size only while it remains inside its parent content area and leaves required sibling gaps. If neither Auto Size nor safe expansion fits the text, stop with a layout failure and request a content or design decision; never clip, overlap, or add a one-off baseline offset.

Text component: TextMeshPro is the default in the primary references (knife-tower, monkey-escape). UniText is an EXPERIMENT in one reference project, not a team decision: the user is testing whether it performs better than TMP and whether its right-to-left support (Arabic etc.) makes localization easier. that project has no localization yet and nothing has been measured, so neither is proven better. Use the component the current project already uses; do not migrate between them or claim a performance or RTL advantage without a measurement (`profiling-evidence`). Keep text creation behind one shared factory so the choice can be swapped, and fix the baseline offset there, not per label.

## Automatic fitting

Always pair this skill with `ui-text-autofit-system`: the project must have `UI_TextAutoFit` installed so auto size, padding and overflow are handled automatically. Do not hand-fit texts.

## Outline is mandatory on EVERY text
- No text may ship without the black outline material (white/coloured face + dark outline), on every screen, popup, tab, button, price, small helper line and world label; without it text is unreadable on bright art. When creating, cloning or restyling any TMP, assign the outlined preset immediately.
- Verify by script on the live screen: every active TMP's material has outline width > 0 (or an underlay); list offenders by hierarchy path and fix at the shared source (prefab/builder/text factory), not per instance. A screenshot showing plain-white text on a light surface is a defect to fix at once (auto-fix loop in `ui-always`).

## One shared outline material, light outline + lower dilate (owner rule 2026-11-09)
Thick black rims on big text look heavy and clumsy, but the game must stay light on low-end mobile: ALL UI labels share ONE TMP material instance (never one material per size class). Tune a single pair that works from 26 px labels to 90 px amounts: outline ~0.30, face dilate ~0.28 (TMP SDF `_OutlineWidth`, `_FaceDilate`), soft navy-black outline colour, light black underlay. Lowering the outline alone fattens the white fill (counters of 6 / 5 / 2 close): always lower the face dilate with it. Verify on a 1920x1080 Play screenshot at small and huge sizes; if one pair cannot satisfy both, ask the owner before adding a second material.

## Black haze behind text = fix on sight (owner rule 2026-11-11)
A dark halo / smear behind a label (hard black UNDERLAY drop shadow, outline width >= 0.7, face dilate >= 0.5) is a defect wherever it is seen, in any screenshot or audit: fix the ROOT first: the TMP_SDF shader alpha-clip patch (`tmp-shader-alpha-clip-fix`, game-wide), then the shared TMP material, never per label. Check `UNDERLAY_ON` and `_OutlineWidth` / `_FaceDilate` / `_UnderlayColor` alpha of the font materials; target outline ~0.30, dilate ~0.28, navy-black outline (0.04,0.06,0.14), underlay off or alpha <= 0.35 with softness ~0.25 and offset |y| <= 0.5. Then screenshot small and large text in Play.

## Every TMP has the outline (owner rule 2026-11-11, automatic)
Every TextMeshPro text, UGUI and world, ships with an outlined material (outline width > 0.01). The agent fixes it by itself whenever it SEES an outline-less text (screenshot, dump or prefab inspection), never waits to be told and never writes a project C# tool for it:
1. Find: one-off Editor script via MCP over first-party prefabs + open scene, list TMP whose `fontSharedMaterial` has `_OutlineWidth <= 0.01`.
2. Fix at the source prefab: assign the outlined material of the SAME font asset (same atlas); never a different font. If the font has none, make one outlined material for that font and reuse it.
3. Keep the TMP_SDF shaders patched with `max(alphaClip..., 0.01)` (`tmp-shader-alpha-clip-fix`).
4. Report counts before/after and what was left (fonts without an outlined material).

## Thin/pale text right after a popup opens (owner 2026-11-13)
TMP bakes scale-dependent SDF data (outline width, softness) into the mesh. A popup that opens by scaling (0.3 -> 1) keeps the small-scale mesh, so labels look thin and pale for a while until something rebuilds them. Fix: a component on the popup root that waits for the scale to settle, then calls `SetVerticesDirty()` on every child TMP once; guard with a test over all popup prefabs. Do not guess (glyph preload, material swaps did nothing): reproduce by saving frames with `ScreenCapture.CaptureScreenshot` from an `EditorApplication.update` callback and compare crops. Material/outline values read back constant, so numbers alone hide this bug.
