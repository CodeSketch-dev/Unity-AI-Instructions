# Break-and-Steal reference foundation profile

Verified from `D:\GitProject\thunder-break-egg\break-and-steal-unity` (read-only):

Use this profile for SketchEngine v2 package/API semantics and as the authoritative visual reference for Roblox-style environment/map work: shader/material, vertex-color baking, and mesh combining. It is not an authoritative source for code house style, naming, boot ownership, UI structure, pooling choices, or gameplay architecture.

- Unity 6000.3.22f1, URP 17.3, SketchEngine v2 (`com.sketchengine`), `namespace Game`.
- `GameSingleton`, `UIGlobalCanvas`, `SceneLoaderPlus`, and `LoadingScreen` preserve the persistent-root/global-UI/scene-loading architectural intent of the v1 references.
- `Character : OptCollisionSensorFast<ICharacterCollidable>` remains the moving collision owner, while world interactions use non-generic `OptCollisionRegister` plus interface families such as `ICharacterCollidable`.
- `DataBlockWarmup` runs before scene load; it uses generated registrations for builds and reflection fallback in the Editor. Do not copy the v1 `DataBlockPreloader` into v2.
- This project uses distributed static boot hooks (for example `Game_Settings` and scene-aware BGM bootstrap), which is an implementation fact—not a target architecture requirement.
- Data, factories, `StaticBus<TEvent>`, state machines, and audio factories remain framework-owned contracts. `MonoCached` provides cached Unity references; inspect the actual tick owner before using `Tick` hooks.
- The manifest includes UniTask, PrimeTween, Addressables, Localization, and Ivan Murzak Unity MCP, but optional dependencies must still be detected per target project.
