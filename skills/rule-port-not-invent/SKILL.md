---
name: rule-port-not-invent
description: "Standing rule: port a reference game's visuals, prefabs, audio and UI exactly and never invent what a sister project already has. Use before creating any icon, HUD tile, arrow, pickaxe, popup or sound for a clone."
---

# Port, do not invent

The most repeated correction in thunder-break-egg (report 11, user feedback): "close enough" art and improvised icons were rejected and reworked. Why it matters here: the user's goal is a faithful clone, built fast and right the first time.

1. **Check the reference first**: the reference game's prefab/atlas/audio, then the sister projects (`reference-index`). Generate new art only after proving none exists and say so.
2. **Transfer the full closure** (prefab + materials + shader + textures + animator) with GUIDs, through `asset-transfer-closure`, with a SketchEngine adapter instead of copying a CodeSketch class. Log provenance in `docs/asset-provenance.md`.
3. **Procedural art copies the silhouette language** of the reference (voxel pickaxes, not smooth chamfers; square tips, not cones); every tier distinct; delete superseded art instead of keeping it.
4. **Repeated art** = one mesh + vertex colour + shared material, baked in the Editor, authoring objects kept for re-bake (`vertex-color-baking`).
5. **Use installed frameworks** (Audio, Popup, Taptic); transfer only the clips actually needed.
6. **Do not override the scene's lighting at runtime**: the scene is the source of truth (an agent forced a 1.5 sun; the user removed it). Do not optimise a shader that renders correctly on device (black characters came from stripping one).
7. When unsure which source wins: reference priority is the original game footage, then knife-tower/monkey-escape conventions, then tuned "fun".

Workflow: `reference-port` (compare side by side), `game-clone-recon`, `clone-ip-safety` for what must not be copied. Ledger of the underlying corrections: `user-corrections-ledger`.
