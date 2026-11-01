---
name: urp-renderer-feature-review
description: "Review a URP Render Graph ScriptableRenderPass or renderer feature: material and texture binding, static render function, PassData init, descriptor reuse, input requirements. Use when writing, porting or debugging a custom URP pass (Unity 6)."
triggers: render graph, renderer feature, scriptable render pass, recordrendergraph, passdata, texturedesc, blit pass, fullscreen pass, custom urp pass, rendergraph review, tinh nang renderer, pass tuy chinh
---

# URP Render Graph renderer feature review

Source: official (Unity-Technologies/skills/validate-urp-render-graph-renderer-feature), re-written; the checklist is short on purpose.

## Inputs
Unity and URP version, the feature + pass code, intended input/output, constraints. Do not invent APIs: check the installed URP package source for the exact signatures.

## Checklist (report each as confirmed, risky or missing)
1. Material binding: the material is created or assigned once, null handled, and EVERY shader input is bound each recording, including the primary source texture (not only masks/noise). Property names match the shader.
2. Resource roles: textures read via `UseTexture` are inputs; targets written via `SetRenderAttachment` are outputs; source, destination and auxiliary textures are not mixed up.
3. Static render function: it is `static`, reads only the PassData/context it receives, no instance state.
4. PassData: every field used by the render function is assigned in each `RecordRenderGraph` call; PassData is per-recording, never persistent, no stale handles from earlier frames (it is pooled).
5. Descriptors: derive from a graph resource (for example the active colour texture descriptor) and change only what must differ (name, depth bits, format, MSAA). Avoid building a fresh `TextureDesc` from width/height or camera descriptor by default.
6. Copy and blit passes: use the built-in blit helpers where they fit instead of hand-rolled copy passes.
7. Global resources: expose with the proper API only when other passes need it.
8. Inputs: declare required inputs (depth, normals, opaque colour) via `ConfigureInput` so URP produces them; they also cost bandwidth on mobile.
9. [ours] Mobile: avoid extra full-screen passes on low tier (gate by device tier, see `device-tier-policy`), keep MSAA/resolve cost in mind, avoid reading the camera target while writing it on tile GPUs.

## Output
Summary, confirmed issues, risky assumptions, fixes with corrected snippets, missing info. Verify by entering Play, enabling the feature, Frame Debugger pass list, Console clean, screenshot before/after.

## Guardrails
Do not rewrite working code for style; do not assume Compatibility Mode APIs (Execute/OnCameraSetup) apply on Render Graph.
