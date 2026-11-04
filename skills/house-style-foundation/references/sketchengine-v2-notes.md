# SketchEngine API notes (installed package semantics)

Verified in a Unity 6000.3 / URP 17.3 project using `com.sketchengine` (the upgraded framework), `namespace Game`. Use this file for API semantics and for Roblox-style environment work (map composition, shader/material, vertex-color baking, mesh combining). It is not a source of code house style, naming, boot ownership, UI structure or gameplay architecture: those come from the primary reference (`reference-profile-v1.md`) translated by the table there.

- Namespaces seen in the package: `SketchEngine.Mono` (`MonoSingleton<T> : MonoCached`, abstract `PersistAcrossScenes`, `Instance`, `SafeInstance`), `SketchEngine.SO` (`ScriptableObjectSingleton<T>` loads from `Resources/<root folder>/<TypeName>`), `SketchEngine.Data` (`DataBlock`, `DataValue`, `DataBlockWarmup`), `SketchEngine.Patterns.Observer` (`StaticBus<T>`), `SketchEngine.Optimize` (`OptCollisionRegister`, sensors), `SketchEngine.Audio`, pool and popup namespaces. Re-check these against the installed version.
- `DataBlockWarmup` runs before scene load; generated registrations for builds, reflection fallback in the Editor. Do not copy the v1 `DataBlockPreloader`.
- `Character : OptCollisionSensorFast<ICharacterCollidable>` stays the moving collision owner; world objects use the non-generic `OptCollisionRegister` plus interface families.
- `MonoCached` caches Unity references and declares virtual `Tick/LateTick/FixedTick` hooks; inspect who dispatches them in the installed version before relying on them.
- The package also ships Internet and Notification modules: check them before writing a custom internet gate or local notifications.
- Boot may be distributed over static hooks (settings binder, scene-aware BGM bootstrap) in some projects; that is an implementation fact, not a target architecture. Document the actual hook order instead of inventing a central class.
- Optional dependencies (UniTask, PrimeTween, Addressables, Localization, MCP) must still be detected per target project from `Packages/manifest.json`.
