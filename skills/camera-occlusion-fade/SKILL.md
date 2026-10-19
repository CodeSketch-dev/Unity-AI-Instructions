---
name: camera-occlusion-fade
description: "Cheap third-person occluder fade: segment-vs-bounds test on a registered target list every 0.05-0.1 s, hysteresis, shared transparent twin material, instant or timed fade. Use when props or models block the player view."
---

# Camera occlusion fade

Extends the occluder note in `freelook-third-person-camera`. Goal: things between camera and player turn translucent without physics queries or per-object material instances.

1. **Register, don't search**: fadeable objects (selected props, pets, big models) add their renderers to a static `OcclusionFade` list on enable and remove on disable. No raycasts, no `FindObjectsOfType`.
2. **Test**: every 0.05-0.1 s (not per frame) test the segment camera -> player-focus point against each registered renderer's `bounds` (expanded slightly; skip those farther than the camera distance or behind the camera). Zero allocation, `sqrMagnitude` only.
3. **Hysteresis**: fade out as soon as hit; fade back only after N clear ticks (about 0.2 s) to stop flicker at edges.
4. **Material**: keep each renderer's opaque shared material and a **shared transparent twin** (one per source material, cached in a dictionary, same textures). Swap `sharedMaterial` references (SRP Batcher safe); never `.material` (instances). Alpha target about 0.3.
5. **Variants**: instant (swap twin at fixed alpha, like a switch) for cheap/low tier; timed (lerp a shared alpha only when a MaterialPropertyBlock-free path exists, else step through 2-3 twin alphas).
6. **Extras**: hide outline/shadow-caster/extra passes while faded; restore all on disable, on pool return, on scene unload (`scene-teardown-safety`). A pooled object returning faded is a bug.
7. **Scope rule**: decide which categories fade (e.g. only objects inside a zone) and which never do (bosses, targets); put it in a flag on the registrant.
8. **Tests**: keep the fade decision a pure function (segment, bounds, hysteresis state -> fade bool) and cover enter, exit, flicker edge, and disabled-while-faded in EditMode.
