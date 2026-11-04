# Reference project matrix (roles, not names)

Read-only audit set. Project names live only in `PROVENANCE.md`.

| Role | Framework | Shared contract | Important delta |
|---|---|---|---|
| Primary house-style reference | v1 (`com.codesketch`), Unity 6000.0, URP | persistent root + global UI, `Factory_Audio`, BGM helper, `SceneLoaderPlus`/`LoadingScreen`, `CameraManager`, localization factories, pooled runtime objects, collision registry, `DataBlock`/factories/events/state | most complete reference for the global Canvas, popup/UI, device policy, pool initialisation and multi-interface collision registers. See `reference-profile-v1.md` |
| Second v1 confirmation | v1, Unity 6000.0, URP 17.3 | same API family, same singleton/global UI, audio/BGM, loading, camera, localization and collision-registry pattern | corroborating evidence; loading lives under a feature-specific path, so do not hard-code feature paths. See `reference-profile-v1-confirmation.md` |
| SketchEngine API reference | SketchEngine (`com.sketchengine`), Unity 6000.3, URP 17.3 | API semantics plus the Roblox-style environment visual reference: map composition, shader/material, vertex-color baking, mesh combining | confirm code APIs against the installed source; do not derive naming, boot, UI, pooling or gameplay architecture from it. See `sketchengine-v2-notes.md` |

## Shared generation rules
- Inspect the target manifest and one installed API example before writing framework code; prefer the SketchEngine form of every pattern.
- Derive code house style from the primary reference and the second confirmation; use the API reference to validate SketchEngine calls and for environment/render work.
- Keep persistent-root / Canvas / popup hierarchy and service ownership project-agnostic in the profile; keep namespace, generic arguments, singleton casing, base classes and asset paths version-specific (read the package).
- Treat UI, audio, localization, scene loading, camera/input, collision, data/factory/events/state/pool and QA/mobile policy as leaf skills; load only the leaf the current GDD task needs.

## Do not merge across framework versions
- Do not copy a v1 generic `OptCollisionRegister<T>` into SketchEngine or remove the generic argument from a v1 project.
- Do not assume `Instance` vs `INSTANCE`, `MonoBase` vs `MonoCached`, or singleton asset folder names until the target package is identified.
- Do not treat project-specific minigames, popup names, audio clips or scene folder names as reusable foundation contracts.
