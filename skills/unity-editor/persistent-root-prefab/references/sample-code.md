# Sample code (SketchEngine form; check the installed package API first)

```csharp
// Scripts/Logic/Game/GameSingleton.cs  (the whole file; no logic)
using SketchEngine.Mono;
namespace Game
{
    public class GameSingleton : MonoSingleton<GameSingleton>
    {
        protected override bool PersistAcrossScenes => true;
    }
}
```

```csharp
// Scripts/Logic/Game/GameMasterInit.cs
using UnityEngine;
namespace Game
{
    public static class GameMasterInit
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void RuntimeInit()
        {
            if (Application.isMobilePlatform)
            {
                Application.targetFrameRate = Mathf.Min(Screen.currentResolution.refreshRate, 60);
                QualitySettings.vSyncCount = 0;
            }
            DevicePolicy.ApplyRenderPolicy();   // see device-tier-policy
            InitSettings();                     // bind saved volume/vibration to audio + haptics
        }
        static void InitSettings() { /* project binding of the settings Data values */ }
    }
}
```

```csharp
// Duplicate-safe derived singleton child (hazard: this Awake body also runs in the doomed copy)
public class GameManager : MonoSingleton<GameManager>
{
    protected override bool PersistAcrossScenes => true;
    protected override void Awake()
    {
        base.Awake();
        if (Instance != this) return;          // duplicate copy: do nothing else
        StaticBus<Event_Home_Return>.Subscribe(OnHomeReturn);
    }
    protected override void OnDestroy()
    {
        if (Instance == this) StaticBus<Event_Home_Return>.Unsubscribe(OnHomeReturn);
        base.OnDestroy();
    }
    void OnHomeReturn(Event_Home_Return e) { }
}
```
Notes: `Instance` returns the first registered instance, so `Instance != this` is true in the duplicate. Verify the `StaticBus` method names and namespaces in the installed package. The installed `MonoSingleton<T>` derives from `MonoCached`, has `[DefaultExecutionOrder(-50)]`, virtual `Awake`/`OnDestroy`, `Instance` (falls back to a scene search, never auto-creates), `SafeInstance` (creates a `[Singleton] T` object: avoid it for scene-authored managers), `HasInstance`, `IsDestroyed`, `Attach(Transform)`.

Boot-scene hook (boot controller or a partial class of the vendor splash): warm saves, wait the gate, `SceneManager.LoadSceneAsync(1)` (Home = build index 1).
