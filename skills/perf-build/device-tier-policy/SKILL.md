---
name: device-tier-policy
description: "Use when a low-end Android crashes or runs hot, or when setting up quality tiers: detect Low/Medium/High at runtime and apply render, physics and per-object policies by editing the active URP asset in place, never swapping it."
triggers: device tier, low end, quality tier, low end android, anr, nong may, may yeu, kt style
---

# Device tier policy

The studio ships ONE Quality level ("Mobile", excluded from Standalone) and two URP assets (mobile, PC); tiering is a runtime policy in a static `Device` class (GPU + RAM tier) and a `DevicePolicy` class (see references/PROVENANCE.md). Do not add many Quality levels per tier. Values table and content scaling: [references/tier-table.md](references/tier-table.md).

## Detect the tier (soft defaults)
GPU family from `SystemInfo.graphicsDeviceName` (Adreno number: >=700 High, 690 Medium, >=650 High, >=612 Medium, else Low; Mali/Immortalis/Xclipse/PowerVR/Tegra families), RAM fallback (<3000 MB Low, >=8000 MB High). Editor = High unless a ForceTier cheat is set. Override when a target device list says otherwise.

## Apply policy (once, in an `AfterSceneLoad` hook)
- EDIT properties of the ONE active URP asset in place (depth texture, render scale, shadow distance, HDR, MSAA). NEVER assign `QualitySettings.renderPipeline` at runtime: it rebuilds the whole pipeline and crashed many low-end Adreno/Mali GPUs.
- Under URP the Quality asset's shadow numbers are decoys; edit the URP asset.
- Physics: `Time.maximumDeltaTime = 0.1` for all tiers (anti death-spiral; default 0.333); Low `fixedDeltaTime = 1/30`.
- Frame rate: `Application.targetFrameRate = min(refreshRate, 60)`, `vSyncCount = 0` on mobile.
- Content scaling by tier (NPC counts, floating text batching, decor destroyed or overdraw renderers disabled on Low) and a global shader keyword for heavy features (e.g. normal-map tiling off on Low).
- Keep debug kill switches (`EnableRenderPolicy` etc.) so a Low-end crash can be bisected.

## Gotchas
- Mutating URP asset fields in the Editor writes them to disk and dirties the asset; the Editor forcing High avoids it, a ForceTier cheat does not (restore or snapshot).
- Scene-scoped policies (a mode that tightens depth/HDR/shadows) must snapshot static state and restore it on destroy.
- `globalTextureMipmapLimit 1` halves every texture on all devices: a hidden quality cost and a big memory win; decide it on purpose.
- The Mobile URP asset is looser than the AGENTS.md baseline (HDR on, soft shadows, distance 50); the policy tightens it for non-High tiers.
- Far-clip trigger zones and tier chunk-cull distances (Low 45 m, Medium 80 m, High 150 m defaults) apply to all tiers (`freelook-third-person-camera`, `culling-group-distance`).
- Dead or untrusted items NOT to copy: a policy method that nobody calls (quality-level apply, per-feature Allow* flags), an unused lodBias option, an Adaptive Performance flag without the package.

## Studio additions to consider (absent in the reference)
Thermal/battery and low-memory handling, a runtime FPS auto-scaler, dynamic resolution, texture/mesh/audio import presets (`import-presets`). Add only with evidence (`profiling-evidence`).

Not measured on a device by the mining study. Verify on a real low-end phone before claiming gains.
