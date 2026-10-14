---
name: legacy-antipatterns
description: Catalogue of anti-patterns seen in the legacy projects (climb-tower, bike-obby, vendor modules) with fixes. Use when reading legacy code to port a mechanic, or reviewing code for these smells.
---

# Legacy anti-patterns (do not copy; copy concepts only)

Source: report 10 (labels AP-01..AP-18, file examples VERIFIED there). knife-tower, monkey-escape and thunder-break-egg are the style source; climb-tower and bike-obby are legacy (layout and mechanic ideas, with these smells).

| ID | Smell | Fix in house style |
|---|---|---|
| AP-01 | God class / partial sprawl (1000+ line controllers, `partial` as modularity: AP-16) | focused sibling components under a hub |
| AP-02 | Static god bag (static refs to player, popups, events) | `DataBlock` for data, StaticBus for events, popup manager |
| AP-03 | Singleton overuse | explicit scene owner or factory SO |
| AP-04 | `Find*` / `FindWithTag` in manager init | serialized refs or events |
| AP-05 | Per-frame work without throttle; `Time.deltaTime` in FixedUpdate | events and timers |
| AP-06 | Copy-paste modes and factories (a mode mislabelled, identical seasonal factories) | one generic world factory; thin mode subclass (`minigame` hub pattern) |
| AP-07 | Parallel infrastructure (second event/audio/UI/save system, JsonUtility saves) | reuse the installed data/event frameworks |
| AP-08 | Mixed namespaces, author-name folders, two tween libs, two pool libs | one namespace, one tween lib, framework pool |
| AP-09 | Logging noise (1000+ `Debug.Log`, emoji logs) | gated logger |
| AP-10 | Hard-coded tuning tables | SO curve/config asset |
| AP-11 | Numbers as strings ("1K", "35a") parsed at runtime | typed double/BigNumber + formatter |
| AP-12 | Non-English comments and identifiers | English only (house rule) |
| AP-13 | Per-object collision callbacks + GetComponent | `collision-registry` |
| AP-14 | Runtime `AddComponent` for authored dependencies | author on the prefab |
| AP-15 | Binary-serialized scenes and settings | force text serialization (agent-readable, diffable) |
| AP-17 | No asmdefs under `_Game` | asmdef per layer |
| AP-18 | Swallowed exceptions (`catch { }`) | log and fix the cause |

Positive ideas worth copying from the same projects (G-01..): a mode registry via config SO + enum + factory lookup, thin mode subclasses over a base manager, `Manager + LevelConstructor + Level + GUI` quartets.

Use: when porting a legacy mechanic, extract numbers and behavior, then rebuild in house style (`legacy-framework-mapping`, `reference-port`). Add `m_SerializationMode: 2` checks to project bootstrap (`unity-project-bootstrap`).
