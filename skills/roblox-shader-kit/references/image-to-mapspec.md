# Image to MapSpec

Use this reference only when the current prompt includes map screenshots, a camera capture or a GDD visual reference. Do not run image routing for a gameplay-only task.

## Compact inference pass

1. Record only visible facts: camera framing, horizon, major silhouettes, landmark order, palette blocks, water/lava/sand evidence, paths and readable empty space.
2. Assign each visible surface a stable `surface` id and a shader slot/flag contract. Prefer the shared `map` family; add a family only for a visible shader/runtime constraint.
3. Represent each generated unit as a `part` and assign a `chunk`. Mark moving, animated, toggleable, damageable or independently culled objects `dynamic: true` so they never enter a static merge.
4. Put measurements that are not visible in `evidence` as `unknown`; never infer hidden collision, topology, gameplay or scale from a single image.
5. Emit a MapSpec before creating Unity objects. The builder consumes the spec; it must not silently invent missing parts.

## Surface cues

- Water: only assign when visible evidence supports water; preserve its texture slot, scroll metadata, transparency and culling behavior.
- Lava: only assign when visible evidence supports lava; preserve its texture slot, scroll and emission metadata.
- Sand/ground/brick: use the normal opaque shared path unless the reference visibly requires a separate family.

## Visual gate

After bake, capture the same camera framing at the requested aspect ratios and compare silhouette, landmark order, palette, depth, surface motion/emission and detail density. Record verified and unverified items in the report. A compile pass or a primitive-only blockout is not visual parity.
