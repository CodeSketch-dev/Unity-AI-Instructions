# Monkey Escape reference foundation profile

Verified from `D:\GitProject\monkey-escape\monkey-escape-unity` (read-only):

- Unity 6000.0.79f1, URP 17.3, CodeSketch v1 (`com.codesketch`), `namespace Game`.
- `GameSingleton`, `UIGlobalCanvas`, and `GameMasterInit` confirm the same persistent-root/global-UI and post-scene-load boot ownership used by Knife Tower.
- `Character : OptCollisionSensorFast<ICharacterCollidable>` is the moving collision owner; world interactions use generic `OptCollisionRegister<ICharacterCollidable>`.
- `Factory_Audio`, `SceneLoaderPlus`, and `LoadingScreen` are established global services. Loading code lives under `Logic/Loading`; this path is not a cross-project contract.
- The project confirms v1 `DataBlockPreloader`, `DataBlock<T>`, `ScriptableObjectSingleton<T>`, `StaticBus<TEvent>`, state machines, and pooled runtime-object patterns.
- Use it as corroborating v1 evidence only. Confirm exact package symbols before generation; do not infer a v2 API or a feature/minigame contract from it.
