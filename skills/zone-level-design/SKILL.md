---
name: zone-level-design
description: "Lay out zones, bases, hubs and levels for Roblox-style mobile games: progression gating, scale, walkability, landmarks, kit reuse, performance budgets. Use when building a map/zone or when the layout is cramped, empty or off-scale."
---

# Zone and level design

A clone's map must read quickly on a small screen: where am I, where do I go, how dangerous is it. Build it from reused art, verify it visually in the Editor, and keep it cheap to render.

## Method
1. **Zone ladder**: list zones in progression order with their gate (stat required), recommended value shown in the entry banner, theme (biome/color), content (resources/enemies/shops) and the reward step up. Derive from `docs/gameplay-analysis.md`.
2. **Blockout first**: place scale-correct greybox (use the character's height as the unit), paths, gates, spawn, safe zone, shops and key landmarks. Walk it in Play Mode before decorating.
3. **Readability on a phone**: strong silhouette landmarks visible from the hub; color-coded zones; clear walkable paths with width >= 3 character widths for main routes; no tiny gaps requiring precision.
4. **Distance and pacing**: time to cross a zone at base speed 10-30 s; shops and upgrade boards placed on the natural route; safe zone near the start of each zone.
5. **Reuse the kit**: prefer existing prefabs/materials; build repeated pieces as prefabs with consistent pivots and snap grid; avoid unique one-off meshes.
6. **Decoration**: props at the edges to frame the path; keep the center clear for gameplay; no collider on pure decoration.
7. **Atmosphere**: skybox, fog color/density and ambient light match per zone; fog hides far-clip pop-in and is a perf tool on mobile.
8. **Safe zones/bases**: clear boundary, entry feedback (FX/audio), world-space boards placed per the reference (see `reference-port`) and not overlapping base geometry.
9. **Performance**: static batching/mesh combine for non-moving props grouped by material; baked lighting where possible; occlusion/zone far-clip triggers for enclosed areas; simple colliders; budget draw calls per zone (measure via `mobile-perf-audit`).
10. **Navigation**: if bots use NavMesh, bake per zone and mark gates; otherwise keep waypoints/graph per zone (see `npc-bots-and-enemies`).

## Lessons from real runs
- **Never narrow or block the runner's path.** Shops, boards and props must not sit on the route (running into a stall while carrying/being chased is infuriating); put them against a wall beside the gateway, and size them modestly (a stall one scale too big was rejected twice).
- **Widen, don't rebuild**: when expanding a map, extend the existing segments instead of deleting them; keep modular segments aligned (equal half-width and wall height at every joint) and verify there are no steps between segments.
- **Decor must be visible from the gameplay camera.** A low camera behind tall walls only sees rim decor that towers above them; far-behind decor is wasted. Scale rim trees/cacti up, and also place low props on the ground along the wall base, never close to egg/pickup spawn points (e.g. keep a clear radius).
- **Biome identity**: each biome gets its own decor vocabulary from the reference (e.g. cacti/pyramids/dead trees, snow trees/ice, spires/lava cracks, coral/shells, palms/ferns, crystals/planets, cherry blossoms/bamboo, jungle/mushrooms) rather than one generic set.
- **Skybox and fog match** per biome; fog hides far-clip pop-in.
- Decor performance and chunking: `world-batching-culling`; generating it: `editor-tool-authoring` (one segment per call, save after each).

## Verify
- Capture Scene/Game views (top-down and a few angles) through the editor tooling and compare with reference screenshots.
- Walk from spawn to the last zone: no gaps, no stuck points, gates trigger banners.
- Check scale: compare avatar to doors, stairs, props with video frames of the reference.
- Check on the three HUD test ratios so UI does not hide key landmarks (`mobile-hud-layout`).
