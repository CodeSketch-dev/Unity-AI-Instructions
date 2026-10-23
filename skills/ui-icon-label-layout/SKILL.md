---
name: ui-icon-label-layout
description: Lay out icon + label inside buttons, pills and price plates with a HorizontalLayoutGroup child instead of hand offsets. Use when a button has an icon and text, a currency price, or the text looks off-centre.
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
