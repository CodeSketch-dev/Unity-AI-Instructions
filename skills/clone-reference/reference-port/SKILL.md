---
name: reference-port
description: "Use when porting or matching a reference feature: inspect source contracts, effective collision response and projected size, then compare behavior and visuals directly."
triggers: reference, match 100%, port source, collision response, damage volume, projected ratio, giong game goc, va cham, sai kich thuoc
---

# Reference port

The user's reference is the specification. A feature is done when it matches the reference under direct comparison, not when it merely works.

## Workflow

1. **Locate the reference implementation** (prefab, scene object, script, config) in the reference project. Read-only. Grep by feature name and by strings visible in screenshots.
2. **Extract the facts** into a small table: hierarchy, transform values *and the parent scale that makes them meaningful*, materials/textures, scripts + serialized values, trigger/collider setup, timing/animation numbers.
   Before choosing projection or geometry, record source perspective/orthographic mode, FOV, camera pose/viewport, mesh depth/topology, complete parent transforms and Color Space. A 2D-looking game can use 3D models with 2D physics; replacing its cubes with billboards is a fidelity change. Required evidence: source values plus a matched-camera Play capture.
3. **Understand construction before copying numbers.** Local offsets only make sense relative to the parent's scale, pivot and geometry. If our construction differs (e.g. world-space canvas vs 3D mesh), reproduce the reference *composition* on our own geometry instead of pasting values. Blind offset copying is the usual cause of "overlaps the cage / wrong position".
4. **Decide adapt vs transfer.** Same framework -> transfer (see `asset-transfer-closure`). Different framework or vendor-locked code -> rewrite behavior in the local framework, keep data and look identical.
5. **Implement, then compare.** Capture a screenshot at the same camera angle as the user's reference image and compare element by element: position, size, rotation, color, texture, text, behavior on interaction. List remaining deltas explicitly.
6. **Run `done-means-wired`** before reporting.

## Hard rules from past projects
- **If the reference already has the prefab/atlas/sub-sprite/model, port it and align it exactly.** Do not pick a "similar" asset or improvise. Generate a new texture or model only after you searched the reference and can say it does not exist there.
- **"Looks close" is not done.** Completion requires a Game View comparison against the user's reference screenshot (same resolution/camera) showing position, size, hierarchy, frame and icon all match. Don't claim completion before that comparison.
- **Compare the right thing**: when the user sends screenshots of both the original game and the reference project, those images, not memory, are the spec. Record which screenshot each delta came from.
- **A rejected result stays rejected**: if the user says an element doesn't match, redo it against the reference instead of tweaking the previous attempt.
- Pace and numbers: learn *relationships* from the reference, not absolute values, unless the user asked for exact numbers (`economy-progression-design`).

## Reporting
State which reference files were consulted, which values were copied vs adapted and why, and any deltas knowingly left (with reason). If the user's screenshot shows something you could not find in the reference, say so instead of guessing.

## Pitfalls
- Billboard vs fixed-in-world: check the reference; don't assume.
- Mirrored/back-facing text: check face direction and the sign of the scale.
- **Original-flow gate:** when parity is requested, verify the complete original interaction order (tutorial, upgrades, completion/tap gate, loading, next stage, restart) before enhancements. Do not replace a missing step with automatic progression; label unrecovered behavior unknown and record the chosen reconstruction separately.
- Don't "improve" the design while porting. Do improvements as a separate, labelled step after parity is confirmed.

## Effective contact and size acceptance
- Component flags alone do not establish effective collision response. Trace layer masks, query filters and native ownership against the owner contract before deciding which objects provide solid support or damage overlap. Never invent solid contact for a mechanism specified as damage-overlap; solid weapons in other references remain valid when evidenced.
- Keep semantic role and physical response separate: labels such as “query”, “sensor” or “collector” do not prove a collider is a trigger or query-only. Preserve the source trigger flag and layer independently; query-visible colliders can still be solid. Compare each raw source flag/layer with the final published collider and material for every builder/role path, and verify both query visibility and support/contact against a real control pair.
- Compare otherwise identical runs with and without the damage volume: prove no unwanted displacement, positive damage, and preserved authored support. A test that only confirms the newly written collision formula does not establish parity.
- Size acceptance needs source config and complete TRS plus a live projected ratio at matched camera/aspect. An unchanged mesh or matching serialized scale cannot close a visible size complaint; never guess a resize.
## Migration invariants

- After a backend or component cutover, inventory and update **every consumer** of the old metadata and binding. Required authored/serialized bindings must fail closed with an actionable error; never silently substitute an empty array, zero, or another default for missing required data.
- When splitting, reparenting, or rebasing chunks, preserve full local position and rotation, plus scale where applicable, through export/import. Verify world orientation with asymmetric basis and corner points on both sides, not only the center; center-only checks can hide a lost rotation.
