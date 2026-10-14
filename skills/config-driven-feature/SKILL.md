---
name: config-driven-feature
description: Build a feature end to end data-driven: persistent data, config assets, factory/registry, events, runtime consumer, wiring. Use when adding any system with tunable values, saved state or many entries ("add X system").
---

# Config-driven feature

A feature isn't finished at the C# file; it spans a chain. Walk the chain every time, and match what the current project already does rather than what you remember from another project.

## 1. Inspect first
Find one analogous existing feature in the current project and the installed framework: its persistent data type, config asset type, factory/registry, event publisher + subscriber, async/state-machine owner. Check `Packages/manifest.json`, asmdefs, namespaces and existing `using` lines. Reuse installed utilities (data blocks, event bus, state machine, pooling, singleton base, async helpers). Do not add a parallel save system, event system or FSM.

## 2. The chain
1. **Persistent data**: serializable, ids/values only (no scene objects or transient state); initialize nullable fields without overwriting loaded values; keyed records created lazily.
2. **Config assets**: one authored asset per entry, stored in the project's config folder by feature; shared tuning lives in a registry/factory singleton.
3. **Registry/factory**: read-only accessors, lookup dictionaries built once at initialization with duplicate/missing-id validation; no LINQ or list rebuilding in hot paths.
4. **Events**: use the global bus only for cross-feature notifications; payload set via constructor; every subscribe has a matching unsubscribe in the symmetric lifecycle callback.
5. **Runtime consumer**: focused components (composition) instead of one god class; state machine for real modes; cancellation for async work owned by a component; pooled spawns.
6. **Wiring**: create the assets through the editor tooling, assign references, register in the factory, save the scene/prefab (see `done-means-wired`).
7. **Verify**: compile, Console, Play Mode path, save/load round trip (change a value, restart, confirm it persisted), and a missing-data path (fresh save).

## Naming and layout
Follow the house style in the global instructions (feature-first names, `Data_`, `Factory_`, `Event_` roles, `Assets/_Game/...` folders), but yield to conventions already present in the project.
