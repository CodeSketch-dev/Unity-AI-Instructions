---
name: urp-postprocessing-volumes
description: "URP post-processing with Volumes: setup, scripting rules (overrideState, profile vs sharedProfile), debug checklist, mobile-safe recipes. Use when bloom, vignette or colour grading does not show, or when adding or scripting a Volume in URP."
triggers: urp volume, post processing, postprocessing, bloom not working, tonemapping, color adjustments, vignette, volume profile, override state, global volume, hau ky, volume urp, chinh mau, bloom khong hien
---

# URP post-processing (Volumes)

Source: official (Unity-Technologies/skills/urp-postprocessing), re-written; [ours] marks additions. For glare on ported models also read `art-volume-bloom-parity`.

## Debug checklist (in order)
1. Camera has `UniversalAdditionalCameraData.renderPostProcessing = true` and is a Base camera, not Overlay.
2. A Volume exists with a non-null profile; the effect was added AND its parameter `overrideState` is true.
3. The Volume GameObject layer is inside the camera `volumeLayerMask` (default is layer 0 only).
4. Global volume: `isGlobal` true. Local volume: camera inside its trigger collider; check `priority`, `weight`, `blendDistance`.
5. Bloom and Tonemapping need HDR on the URP asset (`supportsHDR`). [ours] On mobile accept that cost only when bloom is a real feature.
6. Look in Game view: Scene view has its own post-processing toggle.

## Scripting facts
- Types: `UnityEngine.Rendering.Volume`, `VolumeProfile`; effects live in `UnityEngine.Rendering.Universal`. PostProcessVolume / PostProcessLayer belong to the old PPv2 stack.
- Read with `profile.TryGet<T>(out var t)`; add with `profile.Add<T>()` (throws if present: check `Has<T>()` first).
- Every parameter you set needs `overrideState = true` or the Volume system ignores it (most common mistake).
- `volume.profile` clones the asset into an instance for runtime edits; `volume.sharedProfile` edits the asset on disk. Destroy the cloned instance on teardown.

## Mobile recipes [ours]
- Clean: Tonemapping Neutral, tiny exposure lift, Bloom threshold 1.0 intensity 0.2-0.4, optional Vignette. Skip FilmGrain, MotionBlur, DepthOfField, ChromaticAberration on low-end Android.
- Vivid toy look: Neutral tonemap, saturation +15..+30, slight contrast, mild bloom.
- One global Volume per scene, kept in a prefab; per-biome local volumes only when the look must change.

## Verify
Screenshot the same view with the Volume off and on; read the profile values back through MCP; capture a profiler frame (post-processing adds full-screen passes: quote GPU ms only if measured).
