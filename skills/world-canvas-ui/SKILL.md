---
name: world-canvas-ui
description: "World-space canvas boards and slot layouts: strip imported layout groups, scale pixel layouts with pixelsPerUnitMultiplier, z-order, capacity at least data count. Use when building boards, signs or slot grids in the 3D world."
---

# World-space canvas UI

- **Imported UI**: strip LayoutGroup/LayoutElement/ContentSizeFitter before hand-placing children (they rewrite rects on enable: zero-size or vanished buttons). Verify rects in Play, not in the saved scene.
- **Scale**: pixel board into a meter canvas with factor k: multiply every px value by k and set sliced Images' `pixelsPerUnitMultiplier = 1/k`, else 9-slice borders are huge or glitchy.
- Keep the canvas a hair in front of the frame mesh (z-fighting). Set an event camera if the board is tappable.
- **Capacity**: slot count must be >= data count; shrink spacing, never truncate. Size from the largest item, not the average. Test newest-last ordering with the biggest items (symptom: newest item missing while totals stay right).
- Related: `ui-validator`, `text-spread`.
- Text centring: Capline alignment plus the sprite face offset, never a per-label nudge (`ui-text-tmp` Optical centring).
- World buttons need press feedback too: `UIPressPrimeTween` on the button, pointer down/up forwarded by the pass-through (`ui-button-anatomy` World buttons).
