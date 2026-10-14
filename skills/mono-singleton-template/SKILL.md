---
name: mono-singleton-template
description: Write a MonoSingleton scene or persistent manager correctly (Instance vs SafeInstance, base calls, quit guard). Use when adding a manager component that must exist once.
---

# MonoSingleton template

```csharp
public class GameSingleton : MonoSingleton<GameSingleton>
{
    protected override bool PersistAcrossScenes => true;
    protected override void Awake() { base.Awake(); /* init */ }
    protected override void OnDestroy() { /* teardown */ base.OnDestroy(); }
}
```

## Behavior (report 01, VERIFIED)
- `Instance`: cached, else finds one in the scene; does NOT create. Returns null and logs an error once destroyed or quitting.
- `SafeInstance`: finds or creates `[Singleton] <T>`; use only for infrastructure that must exist (MonoCallback, AudioManager pool).
- `HasInstance`: check this in teardown and quit paths instead of touching `Instance`.
- First instance wins; duplicates destroy their GameObject. `IsDestroyed` is set in `OnDestroy`.
- Subclasses MUST call `base.Awake()` and `base.OnDestroy()`.
- `MonoCallback` forwards Update/pause/quit as C# events for non-MonoBehaviour classes (DataBlocks use it).

## Choose well
Prefer a static class or a `ScriptableObjectSingleton` factory when there is no scene state. A MonoSingleton earns its place when it owns scene objects, coroutines or a pool.

## Mistakes
Assuming `Instance` is non-null on the first frame; reading `X.Instance` from another object's `OnDestroy` during quit; inconsistent `PersistAcrossScenes` between scenes; ignoring `IsDestroyed`.
