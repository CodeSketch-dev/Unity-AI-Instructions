---
name: ui-icon-label-layout
description: Lay out icon + label inside buttons, pills and price plates with a HorizontalLayoutGroup child instead of hand offsets. Use when a button has an icon and text, a currency price, or the text looks off-centre.
---

# Icon + label layout

Findings from the earlier UI mining of knife-tower/monkey-escape (handoff UI findings; VERIFIED by script over prefabs, defaults only):

- The icon + text pair is a **HorizontalLayoutGroup child** of the button: child alignment MiddleCenter, control child width ON, control child height OFF, spacing 5 / 10 / 15 by button size. The group is centred in the button; the label is never pushed off-centre to make room (`ui-style-rules`).
- Label lift: the TMP baseline sits low, so raise the label about 5% of the button height. Apply it once in the text factory.
- Icon height <= ~50% of the button's shorter side with a margin all round; keep icon at its preferred size (`preserveAspect`).
- Image layers (background, frame, glow) fill their parent (inset 0); the TMP sits inset ~10 px per side.
- Price plate: currency icon + amount in the same group; unaffordable amount turns red/grey.
- Ad marker: the reference game's ad icon half outside the left edge (popup) or slightly outside the top-right (HUD); never self-drawn "AD" text.
- Verify by script: loop buttons, compare child rect to parent, check overlap; screenshot at 3 aspect ratios (`unity-ui`).
