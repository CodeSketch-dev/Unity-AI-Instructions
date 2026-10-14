---
name: done-means-wired
description: Definition of done for Unity features: wired in scene/prefab, configs created, refs assigned, compiled, exercised in Play Mode. Use before reporting any feature done, or when "can't click / not showing" after delivery.
---

# Done means wired and verified

Most bugs reported after delivery are missing wiring (an unassigned collider, a prefab override left in the scene, a config asset never created), not logic errors. Run this checklist before saying done.

## Checklist
1. **Source of truth**: if the target is a prefab instance, edit and save the source prefab asset, not a scene override (unless explicitly asked).
2. **Wire**: components on the right objects; serialized references assigned (colliders, canvases, cameras, audio, config assets); layers/tags/physics matrix correct; UI raycast targets and EventSystem present.
3. **Assets**: ScriptableObjects/configs/singletons created in the project's conventional location and registered in the factory/registry that consumes them; editor bake/generator steps actually run.
4. **Save**: scene and prefab saved through editor tooling, after reloading from disk if another agent changed them (`multi-agent-coexistence`).
5. **Compile**: trigger a refresh, then read the Console. Zero new errors; investigate new warnings caused by the change.
6. **Inspect**: read back the final hierarchy and serialized fields instead of assuming. Look for null refs and "Missing" entries on the scene instance *and* the source prefab.
7. **Play it**: enter Play Mode, exercise the real user path (click, enter trigger, collect, upgrade), watch the Console, capture a screenshot when the change is visual.
8. **Edge cases**: second use, disable/re-enable, scene reload, no save data, full/empty states.
9. **Report honestly**: list the checks that ran and mark anything not verified (no Editor connection, no device test). Never claim a Play test that didn't happen.

## Extra checks learned the hard way
- **Generator-owned content**: if a builder/installer produces the object, fix the builder and re-run it; never hand-patch generated output.
- **Wiring omissions that look like logic bugs**: missing tap collider on world-space buttons, a reward button never wired to its handler, a factory field left null, a prefab saved but the scene instance overriding it.
- **Stale compile**: wait for the recompile to finish before running a tool you just edited (stale code produced duplicate objects once).
- **Unsaved work**: save the scene after each stage; an Editor hang loses everything unsaved.
- **Open items stay open**: a reported-but-unreproduced bug (e.g. "ad reward button does nothing") remains on the list until reproduced or explicitly closed with the user.

## If the editor connection is unavailable
Make only safe file-level changes, say exactly what remains unverified, and give the smallest next step to verify.

## Anti-patterns
Reporting after only writing scripts; runtime fallback code standing in for authored wiring; fixing a Console error by deleting the offending asset.
