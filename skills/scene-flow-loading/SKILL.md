---
name: scene-flow-loading
description: "Scene flow and loading: boot scene order, loader screen with real plus fake progress, one-time costs behind loading, no blocking SDK init. Use when wiring scenes and startup."
---

# Scene flow and loading

- Boot order: splash, consent on first launch only, init in the background after the first frame, then the first scene straight into gameplay for new players. See `boot-sequence-setup`.
- Loader screen: fade, real progress to the target, short fake fill to 100%, minimum hold, tips from localization.
- Transition ownership: expose a single busy gate (`IsBusy` or equivalent) shared by fade and load entry points; reject re-entry while a transition is active. Clear it in `finally`/completion handling so an exception, cancelled operation, or missing scene cannot soft-lock navigation.
- For externally started async scene work, register/monitor the operation with that same gate instead of creating a parallel loader state.
- Pay one-time costs here: Addressables, glyph atlases, pool warm-up, mesh combining (`mesh-scene-combiner`).
- Cold start budget is a measured target on a low-end device, not a promise (`profiling-evidence`).
- Scene names follow `scene-naming-conventions`; transitions go through one loader API.
