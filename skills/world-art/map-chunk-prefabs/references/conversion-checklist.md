# Conversion checklist: runtime-built world -> authored chunk prefabs

Baseline (before touching anything): git clean, EditMode PASS/SKIP counts, missing-script count, Console state, load time, memory, draw calls / SetPass of the old world (`profiling-evidence`), screenshots of the old world from fixed cameras.

1. Inventory: list every runtime spawn path (builders, streamers, data assets with path strings, `Resources.Load`). For each: what object, how many, which material, which scripts.
2. Decide chunk boundaries (stage, floor, biome tile) and the container name. One chunk prefab per boundary.
3. Editor builder: write REAL objects (boxes with the surface/material component, art prefab instances) into `Assets/_Game/Prefabs/<Feature>/<Chunk>.prefab` using `PrefabUtility`; idempotent; second run = 0 diffs (`editor-bake-safety`, `editor-tool-authoring`). Never write scene-only objects.
4. Merge pass (chunk-anatomy section 3) to meet the object budgets.
5. Place chunk instances under the container in the scene (positions from the old data), save the scene (text serialization).
6. Side-by-side check against the old runtime world: same bounds, collider count and layers, tags, spawn points, nav links; Edit Mode screenshots vs old Play screenshots.
7. Switch the combiner and culler on; compare renderers, batches, SetPass, load ms, memory against the baseline.
8. Delete the runtime spawn path and the data fields holding path strings ONLY after steps 6-7 pass (`tech-debt`: unused-proof first). Delete orphaned generated mesh assets (GUID scan).
9. Gates: 0 missing scripts (scene + prefabs), compile clean, EditMode counts unchanged, Play the full route 5 min with an empty Console, repeated scene-flow test (`scene-teardown-safety`), prefab and scene sizes within budget.
10. Record the numbers (before/after) in the task report.
