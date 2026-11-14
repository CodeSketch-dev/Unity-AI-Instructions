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

## Re-rip of a map that was already tuned (owner correction: "it was optimized before, why is it black now?")
- The previously shipped map is the source of truth for look and budget. Before rebuilding, read its optimizer/bake tool and git log (atlas, vertex-colour bake, cell size, water merge, restored hero meshes) and reuse every decision.
- Raw UE material vectors are graph multipliers, not final colours (a 0.015 grey rendered near-black; the tuned map had navy). Map every ripped material by UE short name to the tuned material (`<name>_vc` first) and take its colour/texture; report the count.
- Landscape: CUE4Parse exports it (Landscape actor -> glb + 16-bit heightmap + layer weightmaps); build a Unity Terrain from the glb vertices. The landscape glb is yawed 180 deg vs static-mesh glbs: verify placement by foliage-on-ground (median dy ~0, most within 1.5 m) before reporting.
- Never report a rebuilt map without a side-by-side capture against the previous shipped map and the original game screenshot.


## Fidelity traps (owner: "many objects are pure white", 2026-11-14)
- Order is fixed: look parity (audit + side-by-side) -> mobile optimization that keeps the look -> player playtest -> NPCs. Never wire gameplay on a map that still shows white/grey objects.
- glTF import splits a multi-material UE mesh into one child renderer per section, each with ONE slot, in UE slot order: run ONE slot counter across all child renderers. Restarting per renderer gives every section material 0 (lighthouse all white, no red bands).
- Hide what the original never shows: /Engine/BasicShapes placeholders (WorldGridMaterial hazard/blocking boxes), *collision* helper meshes, the UE sky dome (its colour is a time-of-day curve atlas; use a scene skybox). Deactivate the GameObject: optimizers often re-enable renderers.
- Audit by script: visible renderers whose material has no texture and colour >= 0.9 white or the 0.7 default grey; list by screen area; target 0 before reporting.
- Checkpoints from UE actors float ~2.4 m above the floor: ground the spawn points and extend trigger boxes down to the floor, and never spawn inside checkpoint 0 (enter never fires). Teleport tests hide both bugs: verify with a walking character.
- Material params: a runtime MID whose parent was never exported resolves to its base name (strip _Masked/_Translucent/_Glossy; pack variants -> <Name>_Basic), then to the mesh's own glTF default slot (named after the UE material). PM_Diffuse (flatten proxy) is often a detail/colormap texture: prefer the real base-colour param (Albedo, Rock Texture) over it.
- Terrain: create the TerrainData asset BEFORE SetAlphamaps (splats written first are saved blank = 100% layer 0); give every TerrainLayer a matte mask map (URP Terrain Lit reads smoothness from diffuse alpha otherwise: mirror-glossy grass/snow). Verify by measuring alphamap share against the source weight maps.
- Material audits on the glTF shader miss textures (it has no _BaseMap): also list renderers still on glb-embedded materials.
