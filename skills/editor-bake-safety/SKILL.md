---
name: editor-bake-safety
description: "Use when an Editor tool bakes many assets (thumbnails, meshes, atlases) from script-execute or a menu: chunk caps, memory checks, one reusable rig, transparency via two-background matte, and what crashed Unity once."
triggers: bake, thumbnail, thumbnails, icon bake, preview render, PreviewRenderUtility, bulk, crash, editor hang, ram, script-execute, transparent background, alpha
---

# Editor bake safety

Lessons from baking 250+ item thumbnails (Unity 6, URP, MCP script-execute):
- NEVER loop hundreds of renders in one script-execute: the Editor reached ~8 GB and hung, MCP stopped answering for hours. Cap work per call (<= 20 items, 2-3 chunks per call at most), call `Resources.UnloadUnusedAssets()` + `GC.Collect()` between chunks, read `Profiler.GetTotalAllocatedMemoryLong()` and stop above ~2.5 GB.
- Guard: bail out when `GraphicsSettings.currentRenderPipeline == null` (null render settings while rendering with a camera in Edit Mode is a prime crash suspect), when playing or compiling.
- One reusable rig per call (camera/PreviewRenderUtility, RenderTexture, Texture2D) destroyed in `finally`; per item instantiate, render, `DestroyImmediate` clone; use `sharedMaterial`, never `.material`/`.mesh` (they instantiate copies). Batch imports with `AssetDatabase.StartAssetEditing/StopAssetEditing`.
- Do not count EXPECTED failures (items with no source mesh) toward an "abort after N consecutive failures" rule, or chunks stop early and silently skip items.
- Transparency: `PreviewRenderUtility.EndStaticPreview` returns an opaque background. Render the same framing twice on black and on white and derive `alpha = 1 - mean(white - black)`, colour = black / alpha (pure function on `Color32[]`, unit-testable). Verify by decoding the PNG (`ImageConversion.LoadImage`) and counting alpha < 13/255, not via Blit.
- A busy Editor importing hundreds of new PNGs looks hung (`Responding=False`): wait and poll `editor-application-get-state`; do not launch a second Unity on the same project.
- Skipping existing files (`overwrite=false`) hides stale bad outputs: scan outputs for the defect and re-bake only those.
- Save-scene dialogs block MCP: discard unsaved scene changes after a bake instead of saving (project hygiene helper), then run the full test suite.
