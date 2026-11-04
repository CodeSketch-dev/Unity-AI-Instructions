# Map and stage recipes 1-7 and reuse closure
Illustrative; verify API names in the installed SketchEngine package.

## 12. Reuse guide: what to bring

Minimal closure for a "zone lane" in a new game (SketchEngine wording; KT-version names only as provenance):
- Scripts: `Checkpoint` + `ICheckpoint` + `Checkpoint_Manager` + `Checkpoint_Static` (genre-neutral), `Data_Checkpoint` (DataBlock), `CameraFarDistanceZone`, `AI_Waypoint` + manager (only if bots), `Scene_Optimizer` + `MeshSceneCombiner` + `DistanceCullManager` + `Tag_SkipMeshSceneCombiner`, `DestroyIfLowEnd`, `PlatformKill`, `Ladder` (optional), `Nav_TraversalLink` (optional).
- Prefabs: `Checkpoint`, `Minigame_SceneCombiner`, a `Wall`, one `Stage` skeleton (copy `Stage 1` hierarchy, delete content), `SafeZone`, `ReturnZone` (optional).
- Assets: one auto-tiling/lego shader + material family (`Materials/Lego Wall`), `World` ScriptableObject + `Factory` list, Teleport assets.
- Pitfalls: (1) baked renderer lists are scene overrides - re-bake after any stage edit; (2) never rely on prefab sizes of KT floors; (3) checkpoint order = hierarchy order; (4) nesting characters inside a chunk pushes depth to 9; (5) duplicate checkpoint managers/classes (KT has `Checkpoint` and `Tower_Checkpoint` that are the same thing); (6) static fields (`CameraFarDistanceZone.s_active`, `Checkpoint_Static.CheckpointCount`) need reset on domain-reload-off; (7) `_ID`/index mismatch between teleports and checkpoints is silent.
- NOT in KT (lean): no streaming/additive chunk loading, no procedural runtime stages, no data-driven stage lists (stage lists are scene hierarchies), no chunk-pool, no Addressables for stages (the Addressables folder exists but stage prefabs are scene-referenced).

---------------------------------------------------------------------------------------------------


## 13. Kit recipes (genre-neutral; each marked with genres)

### Recipe 1 - "Chunk lane" container + chunk anatomy  [genres: speed/endless lane, biome-based collector/thrower with zones along a lane, runner, obby]
To get an authored route of N zones: create a `Lane` GameObject (plain) with a `ZoneRegistry` manager; create a chunk prefab skeleton `Zone_N` = root BoxCollider(trigger) + far-clip zone + children `Floor`, `Wall`, `Decor`, `Props`, `Waypoints`, `Info`; art props nested as prefabs; drag chunks under `Lane`.
Numbers (KT): median 26 GameObjects and ~150 nested instances per chunk, file ~0.9 MB (soft limit 2 MB), hierarchy depth 2-3 for pure geometry (9 with a boss), 12-17 BoxColliders per chunk, far-clip 200-250 m enclosed / 500+ open, 16 chunks per world, route 2.9 km in one scene.
```csharp
// SketchEngine-style, editor-only registry (provenance: Checkpoint_Manager.Load)
public class ZoneRegistry : MonoCachedFast {
  [SerializeField] ZoneMarker[] _zones;
  [Button] void Load() {            // press after reordering chunks
    _zones = GetComponentsInChildren<ZoneMarker>(true);   // hierarchy order
    for (int i = 0; i < _zones.Length; i++) _zones[i].Construct(i);
  }
  public ZoneMarker Get(int i) => _zones[Mathf.Clamp(i, 0, _zones.Length - 1)];
}
```
Why: hierarchy order is the single source of truth; the designer reorders by dragging.

### Recipe 2 - Generator-into-scene for chains and stacks  [genres: tower/climber, obby, runner with turns, tycoon floor stack]
Editor-only `Generate()` that instantiates prefabs with `PrefabUtility.InstantiatePrefab`, accumulates `Turn[]` rotations and offsets, then saves the result in the scene (towers: height += `Floor.Height`; obby: cursor = previous stage end + start offset). Runtime never calls it. Numbers: tower 7-10 floors x 16.6/20 m, `Turn {index, angle}`; obby 248 chunks, 50 turns, 8x1x8 pads between stages, scene 11 MB.
```csharp
[Button] void Generate() {                        // idempotent: clear then rebuild
  transform.DestroyChildrenImmediate(); var cursor = Pose.identity;
  foreach (var (prefab, i) in _chunks.Select((p, i) => (p, i))) {
    cursor.rotation *= TurnAt(i);                // optional left/right/angle
    var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, transform);
    go.transform.SetPositionAndRotation(cursor.position, cursor.rotation);
    cursor.position = go.GetComponent<ChunkEnds>().EndWorld;
  }
}
```
Why not data at runtime: the owner must be able to open the scene and tweak a chunk by hand.

### Recipe 3 - Zone checkpoint + saved progress  [genres: all (lane, tycoon plots unlock order, runner, obby, collector)]
Bring `Checkpoint` (OptCollisionRegister, posts a StaticBus event), `Data_Checkpoint` (Dictionary<mode, DataValue<int>>), manager with clamp/loop getters, `Load()` button. Player-only branch saves `max(index)`, plays FX/sfx/haptic. Respawn = `GetPlayerCheckpoint()`. For tycoon maps: a "plot unlocked" index replaces checkpoints (same `DataValue<int>`); for a runner: the checkpoint is a section start.
```csharp
public void OnTriggerEnterFunc(Character c) {
  StaticBus<Event_Checkpoint_Enter>.Post(new Event_Checkpoint_Enter(this, c));
  if (!c.IsPlayer) return;
  var saved = Data_Checkpoint.Get(); if (_index > saved.Value) { saved.Value = _index; PlayFx(); }
}
```

### Recipe 4 - World/zone list asset with unlock latch and paid fast-travel  [genres: lane games, biome collectors, idle/tycoon (zone unlocks), runner]
`ZoneSet_Asset` (ScriptableObject): id, level required, speed/score tuning, teleport price entries, scene reference (+ cached scene name), editor buttons to add to Build Settings. `Factory_Zones` holds the list. Unlock = latched bool in a `DataBlock` set when level >= required (never relocked). Teleport popup: spawn item prefabs into a ScrollRect for unlocked stages, price or rewarded ad, then set saved checkpoint = id-1 and post a revive event. KT numbers: 3 worlds, level thresholds 0/120/420, 13 teleports per world, price ladder x2 per 1-2 stages.

### Recipe 5 - Per-scene optimizer prefab + bake key  [genres: all 3D]
One `Scene_Optimizer` prefab (children: combiner, distance-cull manager, waypoint/key managers, NavMeshSurface) in every playable scene; one menu item runs every bake step; chunk roots carry the far-clip zone (deepest zone wins); decor gets `DestroyIfLowEnd`; combiner skips tagged subtrees (anything that moves/fades/toggles). Gates: bake is idempotent (second run diffs 0), renderers and SetPass counts before/after, load time. KT numbers: 25-52 baked groups per scene; far-clip 200-750 m.

### Recipe 6 - Prop kit with one shared material and kill/safe volumes  [genres: obby, platformer, runner, collector]
Props are small prefabs of primitive children (MeshRenderer + BoxCollider, no Rigidbody), one shared shader material family with GPU instancing; hazards are one `PlatformKill`-style component (`OptCollisionRegister<ICharacterCollidable>`, calls `character.Kill()` on enter) plus `AnimationSequence`-style rotation for "xoay" obstacles; safe zone = one trigger + VFX child; ladder logic prefab separate from the model prefab. Numbers: 32 props, 3 KB-1 MB, hazard script 22 lines.

### Recipe 7 - Boss/event set piece inside a chunk  [genres: action lane, collector with boss zones, roguelite arena]
Nest a trigger zone prefab (`SKB_Boss_Zone`: trigger + AI + highlight) into a stage; accept depth 8-9; keep rewards and respawn in zone scripts (`SKB_Return_Stage` pattern: once-per-frame guard per character, compact-number reward strings). Do not nest full character prefabs into reusable chunks when avoidable.

---------------------------------------------------------------------------------------------------

