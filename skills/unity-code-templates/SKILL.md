---
name: unity-code-templates
description: Tested framework-free C# snippets: big-number formatter, duration formatter, pool, CullingGroup culler, FPS overlay, press feedback. Use when a task needs one and the project has no equivalent.
---

# Unity code templates

Copy-and-adapt files in `assets/`. They depend only on UnityEngine (and System), use `namespace Game`, `_field` naming, no `private` on methods, `UPPER_SNAKE` constants. **Before using one, check whether the project or its framework already has an equivalent** (a pool, a number formatter, a culling helper) and use that instead; never run two of the same system.

| File | Purpose | Verified |
|---|---|---|
| `NumberFormatter.cs` | `Format(double)` -> `999`, `1.5K`, `12.34M`, ... `Dc`, then scientific; truncates, never shows `1000K`; `FormatDuration(seconds)` -> `3m 05s`, `2h 10m`, `3d 4h` | compiled and unit-checked with 27 cases outside Unity |
| `SimplePool.cs` | minimal generic prefab pool (`Get`/`Release`, prewarm) | not compiled in Unity here |
| `DistanceCuller.cs` | `CullingGroup`-based show/hide of many renderers by distance, event-driven, disposes on disable | not compiled in Unity here |
| `FpsOverlay.cs` | development-only fps / worst frame / memory readout; removes itself in release | not compiled in Unity here |
| `ButtonPressScale.cs` | press shrink and ease-back for UI and world-space buttons without a tween library | not compiled in Unity here |
| `../debug-cheats-menu/assets/DebugCheats.cs` | cheat panel (separate skill) | not compiled in Unity here |

## Use
1. Copy the file into the project's runtime scripts folder for the right assembly; adjust the namespace if the project uses another.
2. Compile through the editor tooling and read the Console (`unity-mcp-workflow`); fix any version-specific API differences (for example `FindFirstObjectByType` vs older `FindObjectOfType`).
3. Wire and verify per `done-means-wired` (assign the renderer list, attach the component, test in Play Mode).

## Extending the library
When a project writes a reusable, framework-independent helper that survived real use, add it here with a short test or a note on how it was verified, and update this table. Keep the files small and dependency-free so they stay portable.
