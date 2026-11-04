# Samples: Data, Factory, _Asset, Event (SketchEngine form)

## Data block (`Scripts/Data/Data_Item.cs`)
```csharp
using System.Collections.Generic;
using SketchEngine.Data;
using UnityEngine;
namespace Game
{
    public class Data_Item : DataBlock<Data_Item>
    {
        [SerializeField] Dictionary<string, Item_Data> _data;
        [SerializeField] DataValue<string> _equipped;

        public static DataValue<string> Equipped => INSTANCE._equipped;

        public static Item_Data Get(string id)
        {
            INSTANCE._data.TryAdd(id, new Item_Data());
            return INSTANCE._data[id];
        }

        protected override void Init()
        {
            base.Init();
            _data ??= new Dictionary<string, Item_Data>();
            _equipped ??= new DataValue<string>(string.Empty);
        }
    }
}
```
Rules: static accessors over `INSTANCE`; `Init()` = `base.Init()` then `??=`; keyed lookup = `TryAdd` then index; session-only values live as `static DataValue<T>` on a `<Feature>_Static` class.

## Authored entry (`Logic/Item/Item_Asset.cs`) and factory (`Scripts/Factory/Factory_Item.cs`)
```csharp
public class Item_Asset : ScriptableObject
{
    [SerializeField] string _id;
    public string ID => _id;
}

public class Factory_Item : ScriptableObjectSingleton<Factory_Item>
{
    [SerializeField] Item_Asset[] _configs;
    [SerializeField] Item_Asset _default;
    [System.NonSerialized] Dictionary<string, Item_Asset> _dict;

    public static Item_Asset Default => Instance._default;
    public static Item_Asset Get(string id)
        => Instance._dict.TryGetValue(id, out var asset) ? asset : null;

    protected override void OnInitialize()
    {
        base.OnInitialize();
        _dict = new Dictionary<string, Item_Asset>();
        foreach (var c in _configs)
        {
            if (c == null) { Debug.LogError("Factory_Item: null entry"); continue; }
            if (!_dict.TryAdd(c.ID, c)) Debug.LogError($"Factory_Item: duplicate id {c.ID}");
        }
    }
}
```
Asset: `Assets/_Game/Resources/SketchEngine/ScriptableObjectSingletons/Game.Factory_Item.asset` (create through the Editor/MCP). Use an Odin `SerializedScriptableObjectSingleton` only when a dictionary or polymorphic data must serialize.

## Event (`Scripts/Event/Character/Event_Character_Dead.cs`)
```csharp
using SketchEngine.Patterns.Observer;
public class Event_Character_Dead : IEvent
{
    public Character Character { get; private set; }
    public Event_Character_Dead(Character c) { Character = c; }
}
// OnEnable:  StaticBus<Event_Character_Dead>.Subscribe(StaticBus_Event_Character_Dead);
// OnDisable: StaticBus<Event_Character_Dead>.Unsubscribe(StaticBus_Event_Character_Dead);
void StaticBus_Event_Character_Dead(Event_Character_Dead e) { /* react */ }
```
