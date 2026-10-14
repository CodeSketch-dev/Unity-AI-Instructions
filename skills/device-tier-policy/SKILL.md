---
name: device-tier-policy
description: Tier devices at runtime (Low/Medium/High) and apply render, physics and per-object policies without swapping the URP asset. Use when a low-end Android crashes, runs hot, or when setting up quality tiers.
---

# Device tier policy

The reference projects ship ONE Quality level ("Mobile"); tiering is a runtime policy (knife-tower `Device.cs`, `DevicePolicy.cs`, report 02, VERIFIED). BSE has Mobile+PC levels, but KT/ME do not.

## Detect the tier (soft defaults)
GPU family from `SystemInfo.graphicsDeviceName` (Adreno number: >=700 High, 690 Medium, >=650 High, >=612 Medium, else Low; Mali/Immortalis/Xclipse/PowerVR/Tegra families), RAM fallback (<3000 MB Low, >=8000 MB High). Editor = High unless a ForceTier cheat is set. Override when a target device list says otherwise.

## Apply policy (once, in an `AfterSceneLoad` hook)
- EDIT the active URP asset's properties; NEVER assign `QualitySettings.renderPipeline` at runtime (tears down the pipeline, crashes many Adreno/Mali GPUs).
- Defaults seen: depth texture High only; renderScale 0.8 on Low; shadowDistance 0 on Low else 50; HDR High only; MSAA 1 on Low; post-processing and depth mode off on Low cameras.
- Physics: `Time.maximumDeltaTime = 0.1` for all tiers (anti death-spiral; Unity default 0.333); Low `fixedDeltaTime = 1/30`.
- Frame rate: `Application.targetFrameRate = min(refreshRate, 60)`, `vSyncCount = 0` on mobile.
- Keep debug kill switches (`EnableRenderPolicy` etc.) so a Low-end crash can be bisected.

## Gotchas
- Mutating URP asset fields in the Editor writes them to disk and dirties the asset; the Editor forcing High avoids it, a ForceTier cheat does not.
- Per-object toggles: destroy decor on Low, disable listed transparent renderers on Low (overdraw), per-camera policy in `OnEnable`.
- The Mobile URP asset itself is looser than the AGENTS.md baseline (HDR on, soft shadows, distance 50); the policy tightens it at runtime for non-High tiers.
- Chunk culling distances by tier in KT: Low 45 m, Medium 80 m, High 150 m (defaults).

Not measured on a device by the mining reports. Verify on a real low-end phone before claiming gains (`profiling-evidence`).
