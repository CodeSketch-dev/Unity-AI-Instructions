---
name: gameplay-polish-recipes
description: "Small reusable recipes: counted input lock, wall-edge decor kit, re-placing ported props, test hygiene traps. Use when locking input during sequences, adding decor to baked maps, or fixing crowded ported layouts."
---

# Gameplay polish recipes

## Input lock without camera lock
- Counted static lock read by the input reader: locked = feed ZERO move/jump/action to the controller, ignore the joystick value (no widget reset, camera look untouched); on release the live value resumes.
- Gate UI button entry points, not the shared attack method that bots also use.

## Wall-edge decor kit on baked maps
- Seed the RNG per chunk (index/side/chunk); measure wall bounds from the scene, never assume axes.
- Overwrite an existing sub-asset mesh with `EditorUtility.CopySerialized` (stable fileIDs, other scenes reuse it).
- Gate each segment by a triangle budget (% of section tris); keep relief < 1 unit so paths never narrow.
- Decor must not overlap spawn points: validate with capsule probes (existing colliders + temporary MeshColliders on collider-less decor) and keep exclusion zones around paths, bosses, gates.

## Re-placing ported coordinates after the area grew
- Dump collider/renderer bounds to a table and render an orthographic top-down PNG with overlays before choosing spots; find a strip with no walk lane; rotate long props; builders enforce transforms every run, not only at creation.

## Test and tooling hygiene
- A layout that derives slot count from item size can drop the newest item: capacity >= data count, shrink spacing instead of truncating.
- Feature configs go in their own folder; a test counting a shared config folder breaks otherwise.
- Grep packages and read back runtime values before adding a "missing" startup setting (frame cap, vSync): the framework often sets it.
- New popups/panels: check the final settled screenshot (1 s after open) for clipping; fix by scaling the panel around its centre.
