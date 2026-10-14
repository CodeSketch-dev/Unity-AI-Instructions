---
name: reference-port
description: "Port or match a feature from a reference project/screenshot faithfully: inspect first, compare side by side, adapt not blind-copy. Use on \"like the reference\", \"match 100%\", or \"ours looks different\"."
---

# Reference port

The user's reference is the specification. A feature is done when it matches the reference under direct comparison, not when it merely works.

## Workflow

1. **Locate the reference implementation** (prefab, scene object, script, config) in the reference project. Read-only. Grep by feature name and by strings visible in screenshots.
2. **Extract the facts** into a small table: hierarchy, transform values *and the parent scale that makes them meaningful*, materials/textures, scripts + serialized values, trigger/collider setup, timing/animation numbers.
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
- Don't "improve" the design while porting. Do improvements as a separate, labelled step after parity is confirmed.
