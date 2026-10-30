---
name: ui-always
description: "MANDATORY first step for ANY Unity UI work - creating or editing buttons, text/labels/TMP, icons, popups, shops, tabs, HUD, currency bars, price plates, scroll boards, prefab layout or UI screenshots (nut, chu, bang, giao dien), including work delegated to subagents. Loads the required UI skill set and the measured-centring gate; never skip, never defer to the user asking."
---

# UI always (hub, mandatory gate)

This skill exists because the UI skills were being skipped. Any task that adds, moves, restyles or fixes a UI element must start here. It is NOT subject to the "load the smallest skill set" lifecycle rule in AGENTS.md: the UI set below is always loaded for UI work.

## Step 0 - Read these before the first edit (Read each SKILL.md; do not rely on memory)
1. `ui-style-rules` - sizes, icon never as large as its button, colours.
2. `ui-center-alignment` - content group centred in its container, <= 1 px, measured by script.
3. `ui-text-tmp` - outline material presets, autosize, Capline alignment, optical centring.
4. `ui-text-autofit-system` - `UI_TextAutoFit`: auto size / padding / overflow handled by the system, never hand-fitted.
5. `ui-icon-label-layout` - icon + label as a HorizontalLayoutGroup content group; icon <= ~50% of the button's shorter side.
6. `ui-button-anatomy` - press feedback, click sfx, grayscale disabled, notify dot.
7. `ui-9slice-buttons` - cutting sprite borders for Sliced buttons/tabs/plates (no notch/seam at any size); read when importing or fixing a button sprite.
Add by task: popups `ui-popup-anatomy`; tabs `ui-tabs`; lists/shops `ui-scroll-board`; HUD `mobile-hud-layout`; reward / watch-ad buttons `ads-popup-flow`; verification `ui-validator`, `ui-visual-qa`.
If a skill file cannot be read, say so in the report; do not pretend it was applied.

### Reading tiers (saves tokens, never skips the gate)
- Tiny tweak (one value, one offset, one label): read ui-always + `ui-center-alignment` + `ui-text-tmp` + `ui-icon-label-layout` only.
- New or restyled button/popup/shop/tab/HUD: read the full Step 0 list plus the task add-ons.
- Matching a reference game: also read the reference directly through its MCP (never from memory or screenshots alone).
Either way the Step 2 gate (measured dx/dy) is mandatory.

## Step 1 - Build rules that are always on
- Every label: outlined font material, Capline alignment (horizontal Center), UI_TextAutoFit on, Raycast Target off, TMP inset ~10 px per side. Never a per-label nudge.
- Icon + label (button, pill, price plate, currency bar, rewarded-ad button): one centred group, spacing 5/10/15 by size; the label sits in the free gap between its neighbours with equal padding; icon height <= 50% of the plate.
- A rewarded-ad button never reads as a plain FREE button: distinct colour, ad icon on the left, label on the right.
- Prefer layout groups over hand offsets; fix the source prefab, then check instance overrides.
- Standing TMP rules: EVERY TMP text has Auto Size ON and a bounded RectTransform (inside its parent, never stretched past the frame; min 10, max <= 0.6 x frame height). Alignment: horizontal Center + Capline, content centred per `ui-center-alignment` (<= 1 px). Every icon + value pill (currency bars, price plates, icon+label buttons) is a HorizontalLayoutGroup content group, not hand offsets.

## Step 2 - Gate before reporting done (mandatory)
1. Run the `ui-center-alignment` bounds script on every changed container: print container centre vs content centre (dx, dy); fail if > 1 px. Also each text: preferred bounds inside its inset at the final font size.
2. Screenshot the Game View in Play and look at it once after the numbers pass.
3. In the report list which skills were read and the measured dx/dy. No measurement = not done.

## Trigger words
button, text, label, popup, shop, tab, HUD, icon, price plate, currency bar, prefab layout, screenshot of UI; Vietnamese: nut, chu, bang, giao dien, canh giua. If any appears, this skill applies even when the user does not mention skills.

## Subagents
When delegating UI work, put in the brief: "Read skills/ui-always/SKILL.md first and the skills it lists, then apply its gate." Paste file paths, not summaries. Reject a subagent report that has no skill list and no dx/dy numbers.
