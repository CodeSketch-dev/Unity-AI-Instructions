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
- Reference world boards (Steal-style SM_InfoBoard + world uGUI canvas) are authored for a ~3.2x scaled world: placed 1:1 in a normal-scale world the board is ~9 m tall and its text sits far above the camera. Scale the board root (0.2-0.25 worked) and enlarge the trigger collider by 1/scale. A uGUI canvas keeps its text readable from any camera angle (3D TextMeshPro is single-sided and vanishes when the camera rotates).
