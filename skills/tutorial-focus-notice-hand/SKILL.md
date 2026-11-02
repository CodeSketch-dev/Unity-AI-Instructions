---
name: tutorial-focus-notice-hand
description: Use when building or fixing a tutorial / FTUE focus layer: translucent black notice frame, focus ring on the target button, pointing hand rules (pivot, mirror, scale-only), notice placement. Keeps every game's tutorial visuals consistent.
triggers: tutorial, ftue, focus, hand, pointer, notice, onboarding, huong dan, ban tay, thong bao
---

# Tutorial focus layer (owner-approved look)

One overlay canvas above popups (sort ~310, below teleport fades). Three parts, nothing else:

1. **Notice** (never a button look): translucent BLACK rounded frame (alpha ~0.85), icon + ONE short white outlined word, frame ~150 px longer than the text so it is easy to notice. Not blue, not tappable-looking. A ribbon (Steal/Break style) is the accepted alternative. Put it HIGH: beside a top-edge button level with it and above the hand; ABOVE a right-side action button (e.g. a hold-to-dig button: "HOLD TO DIG!"). Never in the middle of the screen. Tapping the notice may act as the target.
2. **Focus ring** on the target: gold ring + echo pulse (zoom in/out). The focused button itself may yoyo-scale gently.
3. **Hand**: pivot ON the index fingertip; no sway and no travel (no bob); one fixed diagonal tilt (the sprite's own); ONLY the scale pulses, around the fingertip. The fingertip rests on the button's coloured plate (lower part of the rect), not on the ring edge. Button on the LEFT half: left hand lower-right of it; RIGHT half: mirrored (scaleX -1) right hand lower-left. The hand is the LAST sibling of the overlay: never behind ring, notice or any UI.

Rules: the far-away target gets a reachable button (reveal the travel button during that step), a ground arrow only guides walking. One word per step (kids-first), localized; tests that assert English literals must be updated together with the key. Verify in Play with a screenshot per side (left button, right button, top button) because the hand placement is geometry, not logic.
