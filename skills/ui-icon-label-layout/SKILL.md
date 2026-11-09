---
name: ui-icon-label-layout
description: "Lay out icon + label inside buttons, pills and price plates with a HorizontalLayoutGroup child instead of hand offsets. Use when a button has an icon and text, a currency price, or the text looks off-centre. Part of the ui-always set: read skills/ui-always first for any UI task."
---

# Icon + label layout

Findings from the earlier UI mining of knife-tower/monkey-escape (handoff UI findings; VERIFIED by script over prefabs, defaults only):

- The icon + text pair is a **HorizontalLayoutGroup child** of the button: child alignment MiddleCenter, control child width ON, control child height OFF, spacing 5 / 10 / 15 by button size. The group is centred in the button; the label is never pushed off-centre to make room (`ui-style-rules`).
- Label lift: the TMP baseline sits low and the button lip is thicker at the bottom; compute the exact lift from the sprite border and font cap height (`ui-text-tmp` Optical centring), about 5% of button height as a rough guide. Apply it once in the text factory.
- Icon height <= ~50% of the button's shorter side with a margin all round; keep icon at its preferred size (`preserveAspect`).
- Image layers (background, frame, glow) fill their parent (inset 0); the TMP sits inset ~10 px per side.
- Price plate: currency icon + amount in the same group; unaffordable amount turns red/grey.
- Ad marker: the reference game's ad icon half outside the left edge (popup) or slightly outside the top-right (HUD); never self-drawn "AD" text.
- Verify by script: loop buttons, compare child rect to parent, check overlap; screenshot at 3 aspect ratios (`unity-ui`).

## Containment-first construction

Create `Button/Content/IconLabelGroup` rather than placing the icon and TMP directly on the button. `Content` owns the button’s padded inset; the centred group may use preferred size and the button may expand only if its resulting rect stays inside the parent content area and clear of content siblings. Background, frame and glow layers are decorative exceptions; they may fill their visual parent but never replace the content boundary. After a layout rebuild, reject a label/icon group that leaves its content inset, overlaps another control or needs a per-prefab baseline nudge.

**Mandatory centring:** after any change here, follow `ui-center-alignment` - measure content vs container bounds by script (<= 1 px), and also each widget vs its parent strip (header, plate, row). Fix misalignment yourself; never wait for the user to ask.

## Artwork icons: centre the focal point, not the sprite rect
- Pack/item/hero icons (chest, bag, gem pile) are centred by their VISIBLE content: the alpha bounding box / centre of mass must sit on the centre of the art area (horizontal: card or free box left of the price button; vertical: free band between the top value text and the bonus line/price button), tolerance <= 2 px. Generated or downloaded art often has uneven transparent margins: crop/re-centre the PNG (alpha centroid) before import instead of nudging per card, and remove inherited template offsets.
- Verify per card by script (icon world centre vs art-area centre) and by screenshot; check every tier (small, wide, big card), not just one.

## Two-line labels and secondary buttons on one slot
- A two-line label (name + price/count) needs about 2 x font x 1.46 px of height (Unity UI Text line height). A 30 pt max in an 84 px box spills the second line over the bottom lip: cap the fit max at <= 24 for two lines in a ~96 px button, raise the label box a few px, and verify with `preferredHeight` vs rect height in Play, not by eye.
- When a card slot holds two alternative buttons (e.g. a gem unlock and an ON/OFF toggle), the layout code must place BOTH on relayout. Keeping only the last one in a single field leaves the other at its first-build position and it overlaps the main CTA after a profile (portrait/landscape) change. Track a second reference or a list.
- A tag that repeats the title bar (e.g. "REBIRTH" over a card already titled "REBIRTH 0") and sits beside a single CTA pulls that CTA off-centre: hide the tag and centre the one button.

## Mini buttons with a two-line label (owner fix 2026-11-04)
- Icon (<= 40 px) at left, label box = free gap to the right edge with EQUAL margins (left = icon + 4..8, right ~10); vertical insets: top ~8, bottom ~16 (the sprite lip), so two lines sit on the FACE centre, not on the lip. Cap the font at 24 for 2 lines in an ~84 px button.
- A two-state card (claimed / locked): darken the card plate, texts and icon tint (never grayscale the icon), and grey ONLY the button plate (`targetGraphic.material = GrayMaterial`), labelled CLAIMED / countdown.
- Outline weight: heavy black outlines read as eye-straining; keep TMP outline <= ~0.36 (small) / ~0.52 (large) / ~0.26 (world text) with a navy-black (#14172A-ish) colour and a soft underlay, via cached material INSTANCES (never edit the shared asset).

## Audit false positives and layout facts (2026-11-04)
- Ink audits count ANY child graphic or text as button ink: notification dots, badge counts and glow images must be named so the audit skips them (names containing Dot or Badge), otherwise they shift the measured pair centre. Fix the name, not the layout.
- A runtime icon swap with a raw sprite that has transparent margins shifts the pair: use the tight (alpha-trimmed) sprite and re-fit the HorizontalLayoutGroup after every swap.
- Stacked tile (name / icon / count): the count goes in its OWN row below the icon (>= 6 px gap), the block centred on the tile face using the sprite lip; never put the count over the art.

## Icon never smaller than the text (owner rule 2026-11-09)
In every icon + label / icon + number row the icon height is >= the label font size (visible line height): prefer 1.05-1.25 x the font size, capped to ~70% of the button's short side. A smaller icon sinks next to the text and the label dominates. If space is tight, shrink the TEXT through autofit first. Audit: icon rect height >= text font size for every row (script), then look at the screenshot.
