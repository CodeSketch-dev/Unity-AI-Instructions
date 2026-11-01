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

## Added from open-project-1 (2026-11-02)
Source: third-party example (Unity open-project-1, Apache-2.0), rewritten as ideas.
- Persistent-managers pattern: an initialisation scene loads the managers scene additively once, then the first content scene; content scenes never contain managers.
- Loader takes load requests through one entry point (request carries target scene, "show loading screen", "fade" flags); a fade channel/service brackets unload and load so the player never sees a pop.
- Unload the previous scene only after the fade-out completes, activate the new one before fade-in; reset the busy gate in `finally`.
- Editor convenience: when a content scene is opened directly in the Editor, the loader detects it and loads the managers scene so Play works from any scene.
- Skip (INCOMPATIBLE with our stack): its coroutine and `AsyncOperationHandle.Completed` plumbing; use UniTask (`unitask-callbacks-and-streams`).
