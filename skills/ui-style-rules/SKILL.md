---
name: ui-style-rules
description: Standing visual defaults for Roblox-style mobile UI (icon size, ad badge, text centring, dim, gaps, NEW tag, cards) from past corrections. Use before/after building any popup, shop, HUD button or card, or on "UI looks ugly/uneven".
---

# UI style rules (defaults, each one came from a rejected result)

Standing defaults for the team's Roblox-style look. If the current reference game/spec shows otherwise, the reference wins (`ui-clone`); record the override in `docs/feedback-notes.md`.

## Icons and buttons
- **An icon is never as big as its button.** Glyph (X, arrow, ad camera, coin) <= ~50% of the button's shorter side with a margin on every side; close X on a 104x94 button = ~46 px. Check every `Close`/icon button after a build (script: loop buttons, compare child rect to parent).
- Icon + label are **centred as a group** inside the button (label centred in the button, icon placed to a side only as far as needed to clear the text). Never push the text off-centre to "make room" for a big icon.
- **Ad marker** = the reference game's ad icon (e.g. a red video-camera), no extra pill. On popup buttons it sits half outside the left edge; on HUD buttons it sits slightly outside the top-right corner, vertically centred on the edge line, never covering the main icon or label. Use the reference project's icon, never a self-drawn "AD" text tag.
- Secondary/neutral buttons use the pack's neutral frame sprite, not a tinted coloured button.
- Don't fill the HUD with identical tinted frames: icon (top), label (bottom), badge (corner).

## Text
- Labels are outlined, auto-sized (min/max), and vertically centred in their rect (the font baseline sits low: apply the shared lift once in the text factory, not per label).
- Dark ink text on light panels (names), coloured + outlined text only for rarity / state words. Income lines green, speed lines blue.
- Names that can be long: auto-size, never wrap into the neighbouring control.

## Popups and lists
- Popup dim = black, alpha 220/255 (set in the popup builder AND patched into every existing popup prefab).
- Gaps: list area ends right above the footer button (<= ~20 px gap). A big empty band between list and footer is a bug.
- Rows/cards copy the reference prefab hierarchy (anchors and sizes read from the reference prefab with `ui-popup-from-demo/dump_prefab.py`), not a guess.
- Zone/biome headers: one coloured pill button sprite per biome colour (green/blue/yellow/red/purple/cyan) from the pack, NOT a stretched ribbon sprite (distorts) and NOT a dark text bar.
- **NEW marker**: a small red "NEW" tag generated in the pack style, placed at the card's bottom-right corner, never on top of the card name. Hide it (and any pill behind it) when empty: an empty dark bar looks like a glitch. Never a "!" glyph.
- Locked cards: black silhouette icon, "???" name; selected card: green outline frame.

## Verification
Screenshot every changed popup at 1920x1080, zoom-crop the details the user complained about, and list the rules above that were checked.
