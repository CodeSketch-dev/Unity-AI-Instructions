# World quest arrow ("walk there" steps)

Separate from the focus overlay: the focus pointer handles "tap THIS button", the arrow handles "walk to that place".

- A LineRenderer prefab (two points, width about 1, transparent material with Cull Off, ZWrite Off, scrolling arrow texture) driven by a small guide component that lives in the persistent root's manager group.
- API: `PointTo(start, end, reachThreshold, startOffset, endOffset, localScale, useLowestY, onReached, stopOnReach)` and `Hide()`.
- Stop on reach (distance below the threshold) and call `onReached`; hide on step change or scene exit.
- Terrain-height sampling, endpoints and reach distance belong to the game; see `prefab-dumps/Quest_Arrow.prefab.txt` and `M_Quest_Arrow.mat.txt` for the archived shape.
- Tween helper in the dumps (`AnimationSequence`) is `SketchEngine.Utilities.Animations` in SketchEngine; check the installed namespace.
