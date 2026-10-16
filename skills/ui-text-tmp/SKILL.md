---
name: ui-text-tmp
description: "TextMeshPro conventions: fonts, outline materials, autosize ranges, colors, raycast, number formats. Use when creating labels, titles, counters or fixing text that overflows or looks unlike the reference."
---

# UI text (TMP)

Facts from report 07 (KT 451 TMPs, VERIFIED); defaults, not law.

- **Outline via material presets**, not the Outline component: a bold display font with outline widths ~0.35/0.75/1.0 and a heavier font 15-50, white face, black outline/underlay. World-space text uses the instancing/billboard variant.
- **Autosize on** (about 80% of labels): min 18 almost always, max by role (36-52 common, 72 titles). Use no-wrap and Center/Middle alignment ~88%; do not use Overflow to hide a label that does not fit. Vertical centring: apply the shared baseline lift once in the text factory, not per label (`ui-icon-label-layout`).
- **Raycast Target off** on non-interactive TMPs (82%) and decorative Images.
- **Color**: white face everywhere (87%); accents only for state words: gold F4C046, orange FFA800, yellow F3F300, gray 909090, red FF2C00, green 48FF00. Image tint stays white (97%): color lives in the sprite.
- Dark ink on light panels only for names; coloured outlined text for rarity/state.
- **Numbers**: compact K/M/B via the project `BigNumber` over `DataValue<double>`; set text only when the value changes; count-up tween 0.7 s OutCubic unscaled (`ui-feedback-toasts`).
- Fonts: one display font plus per-locale fonts (`ui-localization`).
- Long names: autosize, never wrap into the neighbouring control. TMP inset about 10 px per side inside its box (`ui-design-tokens`).

## Fit contract

Put every label inside its owner’s padded content area, not directly against a button, Board or Frame border. Resolve TMP preferred bounds after layout: at the configured minimum font, text must remain inside its inset and must not cover another content/control sibling. A button may grow for its preferred icon+label size only while it remains inside its parent content area and leaves required sibling gaps. If neither Auto Size nor safe expansion fits the text, stop with a layout failure and request a content or design decision; never clip, overlap, or add a one-off baseline offset.

Text component: TextMeshPro is the default in the primary references (knife-tower, monkey-escape). UniText is an EXPERIMENT in thunder-break-egg, not a team decision: the user is testing whether it performs better than TMP and whether its right-to-left support (Arabic etc.) makes localization easier. thunder-break-egg has no localization yet and nothing has been measured, so neither is proven better. Use the component the current project already uses; do not migrate between them or claim a performance or RTL advantage without a measurement (`profiling-evidence`). Keep text creation behind one shared factory so the choice can be swapped, and fix the baseline offset there, not per label.
