---
name: data-block-template
description: Author a new persistent data domain with DataBlock and DataValue (Data_X, ??= back-fill, keyed records). Use when adding saved player state such as currency, unlocks, settings or progress.
---

# DataBlock template

Use the installed framework's `DataBlock<T>` and `DataValue<T>`; never add PlayerPrefs wrappers or another save layer (AGENTS.md). Detect the version first (`framework-version-map`): accessor is `Instance` (v1) or `INSTANCE` (v2).

```csharp
namespace Game
{
    public class Data_Currency : DataBlock<Data_Currency>
    {
        [SerializeField] DataValue<double> _gem;
        [SerializeField] Dictionary<string, bool> _flags;

        public static DataValue<double> Gem => INSTANCE._gem;   // v1: Instance

        protected override void Init()
        {
            base.Init();                       // hooks pause/quit save; skipping it loses saves
            _gem ??= new DataValue<double>(0);
            _flags ??= new Dictionary<string, bool>();
        }
    }
}
```

## Rules and why (report 01)
- `??=` every field in `Init`: deserialization does not run initializers, so a field added in an update is null for existing players.
- Keyed records: `Dictionary<string, DataValue<T>>` + `TryAdd` lazily, return the stored record.
- Store IDs and numbers only. No scene objects or `UnityEngine.Object` refs (binary serializer fails), no behavior, no transient runtime state.
- Mutating a collection does NOT mark v2 dirty (autosave fires only on `DataValue.Value` set); it saves only on pause/quit. Wrap hot state in `DataValue` or accept that.
- Renaming or changing a field type can make load fail; load then returns a fresh block (progress loss). Treat as a migration: ask first.
- UI binds with `OnValueChanged +=` and MUST unsubscribe in the matching teardown; the block lives forever.
- Put game-wide blocks in `Assets/_Game/Scripts/Data/`, feature-owned small records beside the feature.
- First `Instance` access pays disk read + deserialize; see `boot-sequence-setup` for preloading.

## Done means
Compiles in Unity, no console errors, the block shows up in the preload/warmup path, and `py -I <skills>/framework-version-map/scripts/framework_inventory.py <project>` lists it. Save facts: `data-persistence-facts`.
