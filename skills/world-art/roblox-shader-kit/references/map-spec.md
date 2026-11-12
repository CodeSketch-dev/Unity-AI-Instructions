# MapSpec contract

`MapSpec` is the compact hand-off between image/GDD analysis and the Unity map builder. It is not a scene dump and it does not contain balance, gameplay state or copied reference-project YAML. Validate its shape with `assets/map-spec.schema.json`, then validate the resulting bake report with `scripts/validate_contract.py`.

## Required decisions

- `source` records whether facts came from an image, a reference project or both.
- `materials` starts with one shared family. Add a family only when transparency, shader state, lighting, culling or runtime behavior makes sharing invalid; record the reason.
- `surfaces` are stable ids mapped to the shader slot/flags and linear RGBA color. The kit protocol uses slots 0..4 and flags 0..31; ordinary surfaces must not receive water/lava slots by convenience.
- `parts` are the smallest authored geometry units. `dynamic: true` excludes a part from static merge. `chunk` is the spatial ownership key; colliders remain separate from the render merge.
- `chunks` carry bounds and optional distance culling. Do not merge objects that move, animate, toggle, receive damage or require independent culling.
- `camera` is reference composition data, not a gameplay camera controller.
- `evidence` keeps verified, inferred and unknown facts visible. Unknown topology must never become hidden generated geometry.

## Bake rules

For compatible static parts, the builder should produce the full shared-material vertex contract: box-mapped metric `uv0`, surface flags/slot/tiling/emission in `uv1`, movement in `uv2`, and linear vertex color. A flat color-only mesh is not an equivalent fallback.

If a surface cannot be represented by the shared shader, use the smallest justified material family and measure the resulting material count, batches, memory and visual difference. Water and lava are surface assignments, not generic color names: preserve their texture slot, movement/emission metadata and transparency requirements.

## Minimal example

```json
{
  "schema": 1,
  "source": {"id": "map-capture-01", "kind": "hybrid"},
  "materials": {"shared": true, "families": ["map"]},
  "surfaces": [
    {"id": "grass", "slot": 0, "flags": 3, "color_linear": [0.18, 0.42, 0.08, 1]},
    {"id": "lava", "slot": 2, "flags": 25, "color_linear": [1, 0.08, 0.01, 1], "emission": 1.5, "scroll": [0.08, 0]}
  ],
  "parts": [
    {"id": "island-01", "geometry": "mesh:island-01", "surface": "grass", "material_family": "map", "dynamic": false, "collision": true, "chunk": "chunk-00"},
    {"id": "lava-flow-01", "geometry": "mesh:lava-flow-01", "surface": "lava", "material_family": "map", "dynamic": false, "collision": false, "chunk": "chunk-00"}
  ],
  "chunks": [{"id": "chunk-00", "bounds": [-32, -4, -32, 32, 12, 32], "cull_distance": 96}],
  "camera": {"position": [18, 14, -22], "target": [0, 2, 0], "fov": 45},
  "evidence": [
    {"fact": "lava exists in the lower-right channel", "status": "verified", "source": "map-capture-01", "impact": "keep lava scroll/emission"},
    {"fact": "hidden collision behind the island", "status": "unknown", "source": "map-capture-01", "impact": "do not invent collider"}
  ]
}
```

The example deliberately contains no game-specific prices, progression or gameplay rules. Those belong to the active GDD.
