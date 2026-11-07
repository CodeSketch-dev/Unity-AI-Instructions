---
name: ue-map-live-fit
description: Use when porting an Unreal Engine game map to Unity and sizes, scales, offsets or models look wrong, or when cutting triangles of ported meshes. Live runtime dump with UE4SS (one key), Blueprint default scales, fit and audit, mesh decimation gates.
triggers: unreal, ue4ss, live dump, blueprint scale, wrong scale, ported map, clone map, decimate, tris budget, skyline, fmodel, cue4parse, ban do, sai ti le, sai scale, giam tris
---

# UE map -> Unity: live fit and mesh budget

## Why static extracts lie
- Instance export (CUE4Parse / FModel / actor CSV) omits values inherited from the Blueprint class: component relative scale, offset, even the visible mesh scale. Example: hammer visual scale 2.0 and offset -7.16 m existed only in the live game; the export said scale 1.
- Placeholder shapes (`Cube`, `Cylinder`, `MI_*Placeholder*`, `Visible=false`) are collision/hazard boxes, never the art.
- Truth check without video: hazard/blocker box = 2 x mesh half extents x scale; pivot radius (`BoundsRadiusCm`) = mesh reach x scale.

## Capture (ONE key)
- UE4SS Lua mod bound to a single key (F8): sample A of every mesh component (world + relative loc/rot/scale, mesh, materials, attach parent), `ExecuteWithDelay(1000)` sample B, then the slow full serialize LAST (it blocks the game thread for 1+ minute, so B before it).
- Struct values need `:get()`; `FindAllOf("StaticMeshComponent")` works; `K2_GetComponentsByClass` returned nothing, use `FindAllOf("ActorComponent")`. Hot reload is off: restart the game after every Lua edit; a Lua string split by a raw newline is a syntax error that silently disables the mod (check `UE4SS.log`).
- Streaming: only loaded actors are dumped; press at several checkpoints.

## Fit
- Static components (world pose identical in A and B): use the dump world transform. Moving actors: actor root x chain of RELATIVE transforms (rest pose), never the one-frame world pose.
- Axes: UE (x,y,z) cm -> Unity (x, z, -y) m; quaternion (x, z, -y, w); scale (x, z, y).
- Reset any per-run counters/caches at the start of every rebuild (a stale counter silently applied nothing on the second run).
- Audit by number, not by eye: for every live component find the mesh in the scene at the expected pose and compare position and sorted scale. Target: 0 scale mismatches, 0 missing.
- Meshes that exist only in the live game (elevator, crane, projectiles): convert GLB -> FBX and generate prefabs automatically.

## Triangle budget (mobile)
- Measure first: sum triangles per mesh x instances; the top 5 meshes were 80 % of 2.6 M.
- Blender decimate with a geometric deviation gate is NOT proof of same look. 15 of 27 decimations failed the Unity depth-compare gate; the skyline looked shattered in a screenshot while the Blender gate said p95 0.2 %. Always run a Unity visual compare against the original and look at a screenshot; keep a backup of the original FBX outside Assets.
- Far decor (skyline, mountains): ship the low-poly proxy as the only mesh (2.8 k instead of 71.8 k); near meshes keep the strict gate.
- Typical budgets: character 6 k, building 4 k, prop 1.5 k, bush/rock 600, grass clump 80, far decor 3 k. View target 300-500 k, hard max 1 M.
- Far skyline must keep its look (glass window grid) at a few thousand triangles: proxy boxes + a world-space grid shader (unlit, SRP Batcher, fog, `fwidth` anti-aliasing) instead of geometry; one shared material. A plain box proxy loses the look and is rejected by the owner.
- Remove art-only statues and teaser props from the mobile map by an explicit rule in the rebuild step (log it), never by deleting source data.
- One capture key only; the mod takes sample B itself 1 s after A and runs the slow full serialize last.

