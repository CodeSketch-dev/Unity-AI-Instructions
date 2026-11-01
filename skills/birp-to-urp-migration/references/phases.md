# BIRP to URP phase gates

Source: official guidance summarized (Unity-Technologies/skills/migrate-birp-to-urp), our wording.

## Inspection snippet list (run through Editor script / MCP, write results to a file)
- Active pipeline: `GraphicsSettings.currentRenderPipeline`, `QualitySettings.renderPipeline` per Quality level.
- Materials grouped by shader name (count). Magenta risk = any shader not in a Built-in converter map.
- Scripts containing `OnRenderImage`, `GrabPass`, `SetReplacementShader`, `CommandBuffer`.
- PPv2 presence: `PostProcessLayer`, `PostProcessVolume` components, `com.unity.postprocessing` in the manifest.
- Lighting: baked lightmaps and probes in the representative scenes.

## Gates
1. Rollback confirmed (state which).
2. URP asset assigned in Graphics and all Quality levels; renderer data present.
3. Supported materials converted; every material's shader listed; unresolved custom/package shaders named.
4. PPv2 settings recreated as Volumes (values read back), PPv2 components disabled or removed.
5. Lighting rebaked or explicitly deferred; probes refreshed.
6. Representative scenes opened and captured after saving; no magenta; Console clean.
7. Quality map: each old Quality level maps to a URP asset with intended shadow, MSAA, HDR, render scale.

## Material conversion notes
- Preserve source data from a pre-conversion snapshot, then restore `_BaseMap`, `_BaseColor`, tiling and offsets after shader change (converters can drop them).
- Particle and fog/smoke materials use Particles/* URP shaders; check blend mode and soft particles.
- Do not trust a converter result for transparent or cutout materials without a screenshot.

## Final wording
"Complete" = all gates pass. "Partial" = URP set up but one of: PPv2 values not recreated, lighting not rebaked, unresolved custom shaders. List them.
