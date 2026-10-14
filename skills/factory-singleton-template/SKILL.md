---
name: factory-singleton-template
description: Create a Factory_X ScriptableObjectSingleton registry/tuning asset and wire it so it exists in builds. Use when adding a feature config registry, shared tuning values or prefab references.
---

# Factory singleton template

```csharp
namespace Game
{
    public class Factory_Currency : ScriptableObjectSingleton<Factory_Currency>   // T must be the class itself
    {
        [SerializeField] GameObject _moreCupPopup;
        [SerializeField] int _receiveMoreCupAmount = 100;
        public static int ReceiveMoreCupAmount => Instance._receiveMoreCupAmount;

        protected override void OnInitialize()
        {
            // build lookup dictionaries here; validate duplicate and missing ids
        }
    }
}
```
Use `SerializedScriptableObjectSingleton<T>` only when you need Odin (dictionaries, polymorphism). Source files in `Assets/_Game/Scripts/Factory/`.

## Wiring (facts from report 01)
- Loaded lazily with `Resources.Load("<Root>/<full type name>")`, so the asset name is `Game.Factory_Currency.asset` under `Resources/CodeSketch/ScriptableObjectSingletons/` (v1) or `Resources/SketchEngine/ScriptableObjectSingletons/` (v2). Under `Assets/_Game/Resources/` is fine.
- In the Editor a missing asset is silently auto-created EMPTY in `Assets/Resources/...`; in a build it is null and the first access throws. After adding a factory: create or move the asset with Unity MCP/AssetDatabase (never hand-write YAML or .meta), assign the serialized fields, then verify the asset exists and fields are non-null.
- `OnInitialize` runs once after load, before `Instance` returns. Do not let a factory and a DataBlock read each other during init (A -> B -> A leaves half-built caches).
- Renaming the class or namespace breaks the lookup name: rename the asset too (GUID references stay).
- Heavy prefab refs in a factory load with it and stay in memory; keep big content behind Addressables.
- Expose values as read-only static properties; no LINQ or list rebuild in hot paths.
- Reset any static caches with `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` for domain-reload-off sessions.

Run `py -I <skills>/framework-version-map/scripts/framework_inventory.py <project>` to list factories with and without assets.
