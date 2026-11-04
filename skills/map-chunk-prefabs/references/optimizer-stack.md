# Optimizer stack (one prefab per playable scene)

```
<Game>_Master                    master prefab: minigame master, GUI loader, BGM starter
|- Optimizer                     Scene_Optimizer (orchestrates the children below)
|   |- MeshCombiner              mesh combine by material (Editor bake of renderer groups, budgeted runtime combine)
|   |- DistanceCulling           distance-cull manager (event driven, culling group)
|   |- WaypointManager           bot waypoints (if the game has bots)
|   |- Keyboard / input manager  (game specific)
|   '- Navmesh                   NavMeshSurface (baked in the Editor)
|- Guide / Tutorial / Treadmill ... game specific children
```
- The combiner and the culler read the EXISTING renderers of the chunks; they never create world objects from data.
- Combine behind the loading screen (budget about 200 ms/frame behind a loader, about 6 ms in play); exclusions through a skip tag and explicit exclude roots; LODGroups disabled after combine.
- Zones: chunk roots carry a far-clip zone derived from the collision register family; when zones overlap the deepest one wins. Applies to every device tier.
- A small shared `SceneCombiner` prefab (combiner + culler + managers) can be dropped into scenes that have no master prefab.
- Baked variant: keep the YAML source scene and the baked scene as a pair, text-serialized, and document which one ships (`scene-optimizer-bake`). Prefer one scene plus an Editor bake step over two diverging scenes.
Related skills: `mesh-scene-combiner`, `culling-group-distance`, `world-batching-culling`, `one-material-world-shader`, `scene-optimizer-bake`.

## Verified details (perf study)
- The bake does more than meshes: one keystroke runs combiner bake, cull-list fetch, NavMesh bake, waypoint build and feature prebakes (`scene-optimizer-bake`). Baked lists are scene overrides on the prefab instance; the prefab keeps empty lists, so re-bake after stage edits.
- Combine runs as a loading-screen task (about 6 ms budget in play, about 200 ms behind a loader) and registers in `Awake` (`mesh-scene-combiner`).
- Chunk culling uses `CullingGroup` per chunk with tier distances (Low 45 / Medium 80 / High 150 m); a chunk culling manager should be a scene-authored prefab, not created with `new GameObject`.
- Tier policy edits the active URP asset in place (`device-tier-policy`); never swap the asset at runtime.
- Dynamic or animated pieces carry the skip tag and are never combined.
