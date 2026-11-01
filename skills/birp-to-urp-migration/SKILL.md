---
name: birp-to-urp-migration
description: "Plan and run a Built-in to URP migration in phases with a rollback gate, material conversion, PPv2 to Volumes, lighting and custom-shader triage. Use when converting a project or scene to URP or fixing pink materials after the switch."
triggers: migrate urp, built-in to urp, birp to urp, pink materials, render pipeline converter, ppv2 to volume, convert shaders urp, grabpass, onrenderimage, chuyen urp, vat lieu hong, nang cap urp
---

# Built-in to URP migration

Source: official (Unity-Technologies/skills/migrate-birp-to-urp), re-written; [ours] marks additions. Details in `references/phases.md`.

## Rules
- Inspect first, do not ask the user to list Built-in features: detect them (active pipeline, PPv2, custom shaders, lightmaps and probes, Quality levels, image effects, command buffers).
- Safety gate: NEVER install URP, assign a URP asset, run the converter or edit materials until a rollback point exists (git branch/commit, archive or copy). Do the Unity version upgrade first, the pipeline change second.
- Treat custom shaders, `GrabPass`, Surface Shaders, `OnRenderImage`, replacement shaders and package-owned shaders as scoped follow-up work, not converter work.
- Pick a deliberate representative scene before validating; a default empty scene says nothing about baked lighting.
- "Complete" only when every gate in the phases file passes; otherwise say "partial" and name what is open.

## Phases (short)
0. Inspect and plan: pipeline state, risks, rollback, representative scenes.
1. URP setup: install/reuse URP, create Mobile and PC pipeline assets, assign in Graphics and every Quality level, convert supported materials (opaque and particle). Verify which shader each material actually landed on.
2. Post-processing: PPv2 to Volumes (see `urp-postprocessing-volumes`), disable PPv2 components.
3. Lighting: rebake lightmaps and probes; compare a screenshot before/after.
4. Custom shaders and render code: port or replace, record unresolved ones.
5. Mobile tuning: SRP Batcher, shadows, HDR, MSAA per `mobile-urp-lighting-baseline`.

## Verify
Console clean, no magenta in the representative scenes (screenshot), Frame Debugger shows SRP Batcher batches, Quality levels all point to URP assets, a build starts. [ours] Keep a before/after screenshot pair per scene in the report.
