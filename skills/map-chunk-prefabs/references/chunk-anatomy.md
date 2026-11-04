# Chunk anatomy

## 1. Tree
```
Scene
|- Stage                         plain container + one manager script (checkpoints / waypoints)
|   |- Stage_0_Lobby [P]         chunk prefab instance
|   |- Stage_1 [P]
|   |   |- (root)                zone / cull component (far-clip zone, cull data)
|   |   |- Wall                  authored boxes (same material family, surface component)
|   |   |- Floor                 authored boxes
|   |   |- Decor                 instances of art prefabs from the source-art folder
|   |   '- Props                 interactive pieces (own scripts, excluded from combine)
|   '- Stage_N [P]
'- <Game>_Master [P]             master + GUI loader + Optimizer child (see optimizer-stack.md)
```
Depth: scene -> container -> chunk -> group -> art prefab -> mesh. Keep nesting depth <= 8 and a chunk root free of gameplay logic except the zone/cull component.

## 2. Budgets (soft defaults; a project may set its own numbers in its config)
| Metric | Default budget | Why |
|---|---|---|
| Renderers authored per chunk | <= 600 | combiner time, memory |
| GameObjects per chunk | <= 1500 | scene load and hierarchy cost |
| Prefab file size | <= 2 MB (flag > 2, fail > 10) | reference worst case was 22 MB |
| Generated or baked mesh asset | <= 20 MB and <= 200k vertices; binary or FBX, never text YAML | load time |
| Scene file | <= 5 MB, text serialized | merge and review |
| Materials per chunk | 1 shared family (+ few specials) | batching |
After every change print the counts with an Editor script (renderers, GameObjects, materials, vertices, file size) and compare with the table.

## 3. Merge adjacent same-material parts (Editor tool, run at authoring time)
Goal: fewer, larger authored boxes. Algorithm sketch for axis-aligned boxes:
1. Collect box-like children of one group with the same material/surface settings, same layer and tag, no scripts, no animation, not interactive.
2. Snap to the project grid, sort by axis, and greedily merge neighbours that share two extents and touch on the third (strip merge), then repeat per axis.
3. Replace the merged parts with ONE stretched box (scale the box, keep the box collider in step), preserve names with a numbered suffix, keep an undo group.
4. Idempotent: re-running changes nothing. Dry run prints "before/after counts" first; write only after the owner or the gate accepts.
5. Never merge parts that move, fade, toggle, are triggers, or are referenced by serialized fields (check references by GUID/instance before replacing).
Result must look identical in an Edit Mode screenshot pair and keep collision identical (ray-cast sample compare).

## 4. Variants and nesting
- Plain prefab per chunk. Variants only for families that differ by art/numbers (floors of a tower). Shared player/character bases may be variants.
- Prefer nested art prefabs over copies; overrides stay small (position, a few numbers).
