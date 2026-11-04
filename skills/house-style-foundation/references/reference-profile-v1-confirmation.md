# Second reference profile (framework v1 confirmation)

Facts read (read-only) from a second hand-authored studio project: Unity 6000.0, URP 17.3, framework v1 (`com.codesketch`), `namespace Game`.

- `GameSingleton`, `UIGlobalCanvas` and `GameMasterInit` confirm the same persistent-root / global-UI / post-scene-load boot ownership as the primary reference.
- The moving actor derives from the sensor (`OptCollisionSensorFast<ICharacterCollidable>`); world interactions use the generic `OptCollisionRegister<ICharacterCollidable>` (v1 form). In SketchEngine the register is non-generic and the sensor filters by interface.
- `Factory_Audio`, `SceneLoaderPlus` and `LoadingScreen` are established global services. Loading code sits under `Logic/Loading` there; this path is not a cross-project contract.
- Confirms the v1 `DataBlockPreloader` (v2 replaces it by `DataBlockWarmup`), `DataBlock<T>`, `ScriptableObjectSingleton<T>`, `StaticBus<TEvent>`, state machines and pooled runtime objects.
- Use it as corroborating evidence only. Confirm exact package symbols before generation; do not infer an API or a feature contract from it.
