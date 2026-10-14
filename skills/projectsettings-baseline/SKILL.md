---
name: projectsettings-baseline
description: Baseline Unity ProjectSettings, physics and URP values for low-end Android and an audit script that flags deviations. Use when setting up a project or when performance or timing looks wrong.
---

# ProjectSettings baseline

Audit with `py -I <skills>/projectsettings-baseline/scripts/projectsettings_audit.py <unity-project>` (read-only; exit 1 on any FAIL). Values are soft defaults from the reference projects (report 02); override with a stated reason.

| Area | Baseline | Source note |
|---|---|---|
| Scripting / arch | IL2CPP, ARM64 | all three refs |
| Graphics API Android | GLES3 + Vulkan (order per project; test both) | KT/ME GLES3 first, BSE Vulkan first |
| Physics | `autoSyncTransforms` 0, `reuseCollisionCallbacks` 1, solver 6/1 (Unity default) | all refs |
| Time | `timeScale` 1, `maximumDeltaTime` 0.1, fixed step 0.02 (1/30 on Low via policy) | BSE had timeScale 20 and 0.333: QA leftovers |
| Frame rate | vSync 0, cap 60 in code | `device-tier-policy` |
| URP | SRP Batcher on, MSAA off/2x, shadowmap 512-1024, 1 cascade, short distance, no soft shadows, HDR off unless required | reference Mobile asset is looser (HDR on, soft shadows, distance 50): audit WARNs |
| Textures | check `globalTextureMipmapLimit` is deliberate (KT sets 1 = half-res everywhere, undocumented) | |
| Layer matrix | keep tight: disable pairs that never touch | the script counts enabled pairs; layout is INFERRED |

## Notes
- Adaptive Performance on in the reference Mobile asset came from the template; decide deliberately.
- The audit reads text YAML only (`DynamicsManager.asset`, `TimeManager.asset`, `QualitySettings.asset`, URP asset found under `Assets/`). It cannot see Build Profiles or Player settings; read `ProjectSettings.asset` for those.
- This is a static check; it does not replace a device test (`profiling-evidence`).
- Android manifest `hardwareAccelerated` fix (ads video views) belongs to `mobile-build-release`, not here.
