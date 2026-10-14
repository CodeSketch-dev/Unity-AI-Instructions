---
name: culling-group-distance
description: Event-driven distance culling with CullingGroup for sprites, world text and small props, plus camera far-clip zones. Use when many small renderers cost CPU or an enclosed stage should render less.
---

# CullingGroup distance culling

Pattern (knife-tower `Keyboard_Chunk_Culling_Manager`, `DistanceCullManager`, report 02, VERIFIED):
1. One `CullingGroup`; set bounding spheres once (`SetBoundingSpheres`), one distance band (`SetBoundingDistances`), `SetDistanceReferencePoint(camera)`, `targetCamera`.
2. Subscribe `onStateChanged`; the handler toggles `Renderer.enabled` / `TMP_Text.enabled`. No per-frame distance loop.
3. Dispose the group and unsubscribe in `OnDestroy`. Re-resolve the camera only when null or changed; cache `Camera.main`.
4. Exclude indicators that must always show (e.g. countdown text).

Soft defaults: sprite/text distance 85 m; chunk distances 45/80/150 m by device tier. A single band can flicker at the boundary: use two thresholds (show below, hide above a larger value, e.g. 420/460 in BSE) for hysteresis (INFERRED improvement).

## Camera far-clip zones
BoxCollider trigger registered through `collision-registry`; entering sets the camera far clip (Cinemachine `m_Lens.FarClipPlane`). Default far 200; small in enclosed rooms, large in open areas. With overlapping zones pick the one the player is DEEPEST inside (min distance to the box faces). Reset the static zone list at `SubsystemRegistration`. Add an editor "fit box to stage" helper.

Baked chunk culling for big static worlds lives in `world-batching-culling`; this skill is the generic small-object case.
