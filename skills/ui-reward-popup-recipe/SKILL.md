---
name: ui-reward-popup-recipe
description: "Layout recipe for small reward / claim / welcome / free-cash popups: stacked plates, cash icon + amount in one HLG, equal-height button pair, x2 sticker near the corner, padding numbers, acceptance checks. Use when building or fixing any popup with an amount and CLAIM buttons."
triggers: reward popup, claim popup, welcome back, free cash, offline reward, claim x2, popup layout, bo cuc popup, nut claim
---

# Reward popup recipe (generic; sizes are 1080 reference px)

**Anatomy, top to bottom, inside the cream body with >= 24 px outer padding on all four sides:**
1. Info plate (muted family, e.g. lavender): one short line ("You were away 1h 22m"). No second currency icon above it when the header already has one.
2. Optional zone/detail plate (only in the full variant).
3. **Reward card in the GOLD reward family**: ONE centred HorizontalLayoutGroup `[cash icon][amount]` (icon first, spacing ~24, MiddleCenter, no fixed text slot, amount uses preferred width and autofits down for long values like `+999.9aa`). The amount is the biggest element on screen (>= 72 px, outline/dilate from the shared material).
4. Button row.
Gaps between stacked rows >= 16 (equal), bottom padding under the buttons about equal to the top padding.

**Button row rules**
- Both buttons the SAME HEIGHT, same baseline, row centred as a group, gap >= 24. Primary (green, rewarded-ad icon, attention pulse) is wider (>= 1.3x width); secondary is blue, never grey (grey reads as disabled).
- Label text is just `CLAIM` on both when an `x2` sticker carries the multiplier. The sticker is a small star badge tucked on the primary's top-right corner (centre pulled INSIDE the corner by ~16 x 8 px), fully inside the window, never over text or the icon.
- Icon height >= label height in every icon + label button; icon + label are one centred HLG on the lit face (skill `ui-lit-face-centring`).
- Every button carries `UIPressPrimeTween`, pivot (0.5, 0.5), click sfx + haptic.

**Acceptance (measure, then look at the screenshot)**: paddings >= 24 / gaps >= 16 by rect math; equal button heights; row centre = content centre; sticker rect inside the window; ink centre of every label within 2 px of its lit-face centre; amount fits its card for the longest value; compact and full variants both balanced; capped / localized strings fit. Put the geometry in pure helpers with EditMode tests (row centring, sticker containment, equal heights).

- Reveal spots (hatch, spawn, reward drop) must keep a minimum distance from the player (~3 m): items placed "at the feet" make the reveal cover the character. Push the spot away along player->spot (fallback: towards the area centre) and keep it inside the area bounds.

## Daily-login day cards: big + horizontal scroll beats "all days visible" (owner correction, twice)
- Fitting all 7+ day cards into one row shrinks them to ~245 px and the owner calls it tiny. Reference (Knife Tower style) day card is ~431 x 617 in a horizontal scroll, today slightly larger, scroll opens centred on today. Size the card group by the free HEIGHT (about 92 %, today's card pulses +5 %), cap at the reference size, let the rest scroll; never size by free width.
- A page-fit helper takes a DESIGN size: give it the reference scroll height (about 700), or the host stays short and the cards cannot grow. After changing the builder, re-bake the modal prefabs and rebuild the UI factory.
- When two old owner notes conflict (big + scroll vs all visible) the newest owner words win; leave the superseded rule in a code comment so it is not re-applied.
