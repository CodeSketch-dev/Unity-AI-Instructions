---
name: config-and-factory-authoring
description: Author config ScriptableObject entries and register them in a Factory with validated lookups, naming and folders, plus a static registry audit. Use when adding authored data entries (skins, items, minigames, pools) to a project.
---

# Config and factory authoring

Extends `config-driven-feature` (the end-to-end chain). This skill is the detail for the authored entries and the registry (report 03).

## Entries
- One asset per entry under `Assets/_Game/Configs/<Feature>/`, role-prefixed names (`Pool_Fx_*`, `Character_<Variant>_*`, `Shop_*`, `Battle_*`, `Wing_*`). Feature subfolders, never loose files in the root.
- Plain `ScriptableObject` by default; `SerializedScriptableObject` only for Odin needs (dictionaries, `[OdinSerialize]`).
- Polymorphic data without Odin: `[SerializeReference] Info _info` plus subclasses and a `TryGetInfo<T>(out T)` downcast.
- Fields `[SerializeField]` private with read-only properties. No runtime state in assets except `[NonSerialized]` caches; persistent state lives in `Data_X.Get(ID)` (lazy `TryAdd`).
- `OnValidate` may derive fields (scene name, mesh from reference prefab); guard against prefab-asset contexts.

## Registry
- Factory = serialized array + `[NonSerialized] Dictionary` built in `OnInitialize` (call `base.OnInitialize()` first). Do better than the reference: ERROR on duplicate id and on null entry, return a clear failure on a missed lookup (the reference overwrites silently or returns null).
- Access by id/enum for authored entries; by named static property for a few UI prefabs (`Factory_Prefab`). `[AssetList(Path="_Game/Configs/<Feature>/", AutoPopulate=true)]` auto-collects a folder (pools); otherwise register by hand.
- Singleton asset path per framework: see `factory-singleton-template` and `framework-version-map`. Create and wire assets through Unity MCP; never hand-write YAML or .meta.
- Project-local conventions win (BSE keeps config classes in `Scripts/Configs/` with `CreateAssetMenu` paths).
- Addressables is installed but unused for gameplay in the reference (INFERRED from a grep of one project). Do not introduce it unless asked; heavy content goes through scenes and the loading flow.

## Audit (read-only)
`py -I <skills>/config-and-factory-authoring/scripts/config_registry_audit.py [--no-fail] <unity-project>` reports: asset in a feature folder that no singleton factory references (`unregistered-config`), duplicate id-like fields in a folder, unassigned prefab/sprite/thumbnail fields, and pool prewarm > max. Output is WARN-level hints: Audio and Pool folders are skipped for registration, and an asset referenced only by prefabs or scenes will show as unregistered. Pair with `framework_inventory.py` (missing singleton assets).
Not covered (needs the Editor): pool prefab lacking `PoolPrefabItem`, scene missing from Build Settings.
