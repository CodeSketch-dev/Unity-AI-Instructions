---
name: ui-text-tmp
description: "TextMeshPro conventions: fonts, outline materials, autosize, colors, raycast, number formats, optical vertical centring. Use when creating labels, titles, counters, or fixing text that overflows, sits high/low in its button, or looks unlike the reference. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# UI text (TMP)

Facts from report 07 (KT 451 TMPs, VERIFIED); defaults, not law.

- **Outline via material presets**, not the Outline component: a bold display font with outline widths ~0.35/0.75/1.0 and a heavier font 15-50, white face, black outline/underlay. World-space text uses the instancing/billboard variant.
- **Autosize on** (about 80% of labels): min 18 almost always, max by role (36-52 common, 72 titles). Use no-wrap and Center/Middle alignment ~88%; do not use Overflow to hide a label that does not fit. Vertical centring: see Optical centring below; set it once in the text factory, never a per-label nudge.
- **Raycast Target off** on non-interactive TMPs (82%) and decorative Images.
- **Color**: white face everywhere (87%); accents only for state words: gold F4C046, orange FFA800, yellow F3F300, gray 909090, red FF2C00, green 48FF00. Image tint stays white (97%): color lives in the sprite.
- Dark ink on light panels only for names; coloured outlined text for rarity/state.
- **Numbers**: compact K/M/B via the project `BigNumber` over `DataValue<double>`; set text only when the value changes; count-up tween 0.7 s OutCubic unscaled (`ui-feedback-toasts`).
- Fonts: one display font plus per-locale fonts (`ui-localization`).
- Long names: autosize, never wrap into the neighbouring control. TMP inset about 10 px per side inside its box (`ui-design-tokens`).

## Optical centring (label looks high or low)

Cause: button/header sprites are 9-sliced with a thicker bottom lip, so the visible face centre sits above the RectTransform centre, and TMP Middle/Midline centres on font metrics, not cap height. Seen in thunder-break-egg: titles about 5 units low, labels with a fixed +5 up to 3 high.

- **Target**: cap-height centre of the text = face centre of the nearest Sliced Image ancestor = rect centre + (border.bottom - border.top) / 2 / (sprite ppu / 100 x pixelsPerUnitMultiplier). Symmetric sprite = 0. Cap centre = baseline + `font.faceInfo.capLine` x font scale / 2.
- **New UI**: set vertical alignment to **Capline** once in the text factory/builder. Measured in Unity: Capline puts the cap centre exactly on the rect centre for any size and string; Middle sits about 0.033 x fontSize high; Geometry/Midline vary with the string. Then the y offset is only the face offset above (0 on symmetric plates). No hand "+5" per label.
- **Existing prefabs**: run `assets/Qa_TextCenter.cs.txt` (copy to Editor/Qa; menu Tools/QA/Center Text dry, then apply). Idempotent. It measures under a temp Canvas (TMP bounds are invalid off-canvas) and edits via `LoadPrefabContents`. It skips multi-line text, layout-group children, non-middle alignment, faces taller than 260, labels far from the face centre, shifts over 7, and plain symmetric frames over 3.5.
- **World text** (3D TextMeshPro, world canvas, nameplates, floating labels): same Capline rule, so the anchor is the visual centre of the caps; put it on the plate/icon centre and add the face offset only over a sliced plate (scale the offset by the label's lossy scale). `Qa_TextCenter` covers UGUI prefabs only; check world text by screenshot at gameplay distance.
- **Verify**: Play, open the popup, screenshot; label centre within about 1 px of the face. Restart Play Mode first: popups created before the edit keep the old layout.
- Leave third-party UI sets alone (different atlases/ppu, measured deltas unreliable).

Default from thunder-break-egg; override when the project's own reference shows otherwise.

## Fit contract

Put every label inside its owner’s padded content area, not directly against a button, Board or Frame border. Resolve TMP preferred bounds after layout: at the configured minimum font, text must remain inside its inset and must not cover another content/control sibling. A button may grow for its preferred icon+label size only while it remains inside its parent content area and leaves required sibling gaps. If neither Auto Size nor safe expansion fits the text, stop with a layout failure and request a content or design decision; never clip, overlap, or add a one-off baseline offset.

Text component: TextMeshPro is the default in the primary references (knife-tower, monkey-escape). UniText is an EXPERIMENT in thunder-break-egg, not a team decision: the user is testing whether it performs better than TMP and whether its right-to-left support (Arabic etc.) makes localization easier. thunder-break-egg has no localization yet and nothing has been measured, so neither is proven better. Use the component the current project already uses; do not migrate between them or claim a performance or RTL advantage without a measurement (`profiling-evidence`). Keep text creation behind one shared factory so the choice can be swapped, and fix the baseline offset there, not per label.

## Automatic fitting

Always pair this skill with `ui-text-autofit-system`: the project must have `UI_TextAutoFit` installed so auto size, padding and overflow are handled automatically. Do not hand-fit texts.

## Outline is mandatory on EVERY text
- No text may ship without the black outline material (white/coloured face + dark outline), on every screen, popup, tab, button, price, small helper line and world label; without it text is unreadable on bright art. When creating, cloning or restyling any TMP, assign the outlined preset immediately.
- Verify by script on the live screen: every active TMP's material has outline width > 0 (or an underlay); list offenders by hierarchy path and fix at the shared source (prefab/builder/text factory), not per instance. A screenshot showing plain-white text on a light surface is a defect to fix at once (auto-fix loop in `ui-always`).
