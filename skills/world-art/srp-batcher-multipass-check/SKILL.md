---
name: srp-batcher-multipass-check
description: Use when URP SetPass calls or batches stay high although objects share materials or were combined. Check the Frame Debugger batch cause for "Node use multi-pass shader" and disable the extra (outline) pass on materials that do not use it.
triggers: setpass, set pass, batches high, srp batcher, multi-pass, outline pass, frame debugger, batch cause, nhieu batch, setpass cao
---
# SRP Batcher multi-pass check

Symptom: SetPass ~ 0.7 x batches even after combining meshes / sharing materials.

1. Open Frame Debugger, click an "SRP Batch" under DrawSRPBatcher, read **Batch cause**. "SRP: Node use multi-pass shader" means an extra enabled pass (OmniShade: `Outline`, LightMode SRPDefaultUnlit) forbids batching and draws every object twice. Script access to Frame Debugger events returns 0 without the real window, so look at it by eye or ask for a screenshot.
2. If the material does not use the pass (OmniShade `_Outline = 0`), disable it per material: `mat.SetShaderPassEnabled("SRPDefaultUnlit", false); EditorUtility.SetDirty(mat); AssetDatabase.SaveAssets();` (persists as m_DisabledShaderPasses). Keep it on materials with a real outline (characters).
3. Measure before/after at the same camera poses (Mobile quality, same method): measured on a street map 314-362 -> 40-53 SetPass, 417-513 -> 189-254 batches, tris also -35% (the outline pass redraws geometry).
Not causes (verified): light/reflection probe mode, MaterialPropertyBlock count 0, SRP Batcher flag on, `ShaderUtil.GetSRPBatcherCompatibilityCode` = 0.
Related cheap win: put small clutter (grass, bushes, small rocks) on a "Detail" layer and set `Camera.layerCullDistances` (~80 m): -25..40% batches, -50% tris at heavy views.
Stats gotcha: UnityStats only refresh when views repaint, and RepaintAllViews also renders the Scene view (numbers inflate), so compare before/after with one method.
