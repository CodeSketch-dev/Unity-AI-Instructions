# Legacy (CodeSketch v1) to SketchEngine translation

Verified against the installed SketchEngine package sources; confirm again in the target project before use.
| Concept | Legacy form | SketchEngine form |
|---|---|---|
| Namespaces | `CodeSketch.Data`, `.SO`, `.Patterns.Observer`, `.Patterns.StateSystem`, `.Patterns.Pool`, `.Optimize`, `.Audio`, `.UIPopup` | `SketchEngine.Data`, `.SO`, `.Patterns.Observer`, state machine type `StateMachine<T>` (check namespace), `.Patterns.Pool`, `.Optimize`, `.Audio`, `.UIPopup`, `.Core.Async`, `.Mono` |
| DataBlock accessor | `Instance` | `INSTANCE` |
| Data preload | hand-written reflection preloader | `DataBlockWarmup` |
| Singleton asset folder | `Resources/CodeSketch/ScriptableObjectSingletons/` | `Resources/SketchEngine/ScriptableObjectSingletons/` |
| Collision register | generic `OptCollisionRegister<T>` (+`2`, `3`) | non-generic `OptCollisionRegister`; sensor `OptCollisionSensorFast<T>` filters `owner is T` |
| MonoCached tick | project-local shadow with public `Tick` called by hand | package `MonoCached` has `virtual Tick/LateTick/FixedTick`; verify who dispatches |
| Singleton base | project class | `SketchEngine.Mono.MonoSingleton<T>` (`Instance`, `SafeInstance`, `HasInstance`) |
| Animation helper | `AnimationSequence` | `SketchEngine.Utilities.Animations` |

Never mass-replace `CodeSketch` with `SketchEngine`: some members were renamed or reshaped. Translate one concept, compile, move on.
