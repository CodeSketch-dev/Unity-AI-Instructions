---
name: legacy-framework-mapping
description: Map legacy CFramework code to CodeSketch and SketchEngine equivalents when porting a mechanic from climb-tower or bike-obby. Use when a legacy script uses CDataBlock, CValue, delegate StateMachine or lowercase instance APIs.
---

# Legacy framework mapping

CFramework (embedded folder, namespace `CFramework`) is the oldest era of the same framework family; CodeSketch and SketchEngine are later versions (report 10). Concepts map 1:1 in most cases; names and some behaviors differ. Never mass-replace namespaces; inspect the installed package and asmdefs (`framework-version-map`).

| Concept | CFramework | CodeSketch / SketchEngine | Port note |
|---|---|---|---|
| Data block | `CDataBlock<T>.instance` | `DataBlock<T>.Instance` / `INSTANCE` | casing: `instance` -> `Instance`; `value` -> `Value` |
| Observable value | `CValue<T>` (`value`, `eventValueChanged`) | `DataValue<T>` (`Value`, `OnValueChanged`) | rename members; v2 skips equal sets |
| Event bus | `StaticBus<T>` | same API | 1:1; pair Subscribe/Unsubscribe |
| Singletons | `Singleton<T>`, `MonoSingleton<T>` | `MonoSingleton<T>`, `ScriptableObjectSingleton<T>` | lowercase `instance` -> `Instance` |
| State machine | delegate-style `StateMachine<T>` | class-per-state `IStateMachine` API | convert delegates into state classes (`state-machine-template`) |
| Mono cache | `MonoCached`, `MonoCachedAll` | `MonoCachedFast`, `MonoCachedHub`, `MonoCachedOpt` | pick by role |
| Pool | `PoolPrefab*` | `PoolPrefabGlobal` + `PoolPrefabConfig` | use configs (`pool-everything`) |
| Config singleton | `FactoryXxx` with `instance` | `Factory_Xxx : ScriptableObjectSingleton` | asset path per version |
| UI | `PopupManager.Create`, `ViewHelper.PushAsync` | same names | check `ui-popup-anatomy` |
| Audio | `AudioManager.Play(AudioConfig)` | same; v2 enum is `SketchAudioType` | |
| Not in CFramework | `MonoCachedFast/Hub`, `CancelToken`, `OptCollision*`, Haptic, data preload/warmup, CullingGroup helpers | present in later versions | add during the port, do not reimplement |

Procedure: 1) list the legacy types used; 2) map each via this table, reading the installed package source for the exact signature; 3) rebuild logic in house style (`data-block-template`, `factory-singleton-template`, `collision-registry`) rather than translating line by line; 4) compile via Unity MCP. Legacy save formats differ (Odin binary vs BinaryFormatter): do not assume old saves load. Not compiled during mining.
