# Reference project matrix

Read-only audit set. Knife Tower and Monkey Escape are the primary house-style sources; Break-and-Steal is an API-semantics and Roblox-environment visual reference.

| Project | Framework | Shared contract | Important delta |
|---|---|---|---|
| `knife-tower-troll-unity` | CodeSketch v1 (`com.codesketch`) | `GameSingleton`, persistent global UI, `Factory_Audio`, `BGMHelper`, `SceneLoaderPlus`/`LoadingScreen`, `CameraManager`, localization factories, pooled runtime objects, `OptCollisionRegister<T>`, `DataBlock`/factories/events/state | Most complete reference for global Canvas, popup/UI, device policy, pool initialization, and multi-interface `OptCollisionRegister2<...>`. |
| `monkey-escape-unity` | CodeSketch v1 (`com.codesketch`), Unity 6000.0.79f1 / URP 17.3 | Same v1 namespace/API family; same singleton/global UI, audio/BGM, loading, camera, localization and collision-registry pattern | Use as a second v1 confirmation; loading is under `Logic/Loading`, so do not hard-code feature paths. See `monkey-escape-profile.md`. |
| `break-and-steal-unity` | SketchEngine v2 (`com.sketchengine`), Unity 6000.3.22f1 / URP 17.3 | API semantics plus authoritative Roblox-environment visual reference: map composition, shader/material, vertex-color baking, and mesh combining | Confirm v2 code APIs against installed source. Use it for environment/render evidence only; do not derive naming, boot, UI, pooling, or gameplay architecture. See `break-and-steal-profile.md`. |

## Shared generation rules

- Inspect the target manifest and one installed API example before writing framework code.
- Derive code house style from Knife Tower and Monkey Escape. Use Break-and-Steal to validate SketchEngine v2 APIs and, when the GDD calls for Roblox-style maps, as the environment/render reference for material, shader, vertex-color, and mesh-combine work.
- Keep `GameSingleton`/Canvas/popup hierarchy and service ownership project-agnostic in the profile; keep namespace, generic arguments, singleton casing, base classes, and asset paths version-specific.
- Treat UI, audio, localization, scene loading, camera/input, collision, data/factory/events/state/pool, and QA/mobile policy as leaf skills. Load only the leaf needed by the current GDD task.

## Do not merge across projects

- Do not copy CodeSketch `OptCollisionRegister<T>` into SketchEngine or remove the generic argument from CodeSketch.
- Do not assume `Instance` vs `INSTANCE`, `MonoBase` vs `MonoCached`, or singleton asset folder names until the target package is identified.
- Do not treat project-specific minigames, popup names, audio clips, or scene folder names as reusable foundation contracts.
