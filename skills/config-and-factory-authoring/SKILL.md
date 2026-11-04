---
name: config-and-factory-authoring
description: Use when adding authored data entries (skins, items, minigames, pools, audio) as ScriptableObject assets registered in a Factory singleton with validated lookups, naming, folders and a static registry audit.
triggers: config, factory, scriptableobject, asset entry, _asset, registry, configs folder, authored data, singleton asset, tao config, dang ky factory, du lieu cau hinh, kt style, knife tower
---

# Config and factory authoring (SketchEngine form)

Extends `config-driven-feature` (the end-to-end chain). This skill is the detail for authored entries and the registry. Templates: `factory-singleton-template`, `data-block-template`.

## Entries
- One asset per entry under `Assets/_Game/Configs/<Feature>/`, role-prefixed names (`Pool_Fx_*`, `Character_<Variant>_*`, `Shop_*`). Feature subfolders, never loose files in the root.
- Class `<Feature>_Asset : ScriptableObject` (plain by default); `SerializedScriptableObject` only for Odin needs (dictionaries, polymorphic data).
- Polymorphic data without Odin: `[SerializeReference] Info _info` plus subclasses and a `TryGetInfo<T>(out T)` downcast.
- Fields `[SerializeField]` private with read-only properties. No runtime state in assets except `[NonSerialized]` caches; persistent state lives in `Data_X.Get(ID)` (lazy `TryAdd`).
- `OnValidate` may derive fields (scene name, mesh from a reference prefab); guard against prefab-asset contexts.
- Only some types need `[CreateAssetMenu]`; create entries through an Editor script or Unity MCP, never by hand-writing YAML or `.meta`.

## Registry
- Factory = serialized array + `[NonSerialized] Dictionary` built in `OnInitialize` (call `base.OnInitialize()` first). ERROR on duplicate id and on null entry; return a clear failure on a missed lookup (legacy code overwrites silently or returns null).
- Access by id/enum for authored entries; by named static property for a few UI prefabs (`Factory_Prefab`). `[AssetList(Path="_Game/Configs/<Feature>/", AutoPopulate=true)]` auto-collects a folder (pools); otherwise register by hand.
- Singleton asset path: see `factory-singleton-template` and `framework-version-map` (SketchEngine: `Resources/SketchEngine/ScriptableObjectSingletons/<Namespace>.Factory_X.asset`).
- If the project already has a config folder convention, follow it.
- Addressables: levels and maps are NOT addressable (prefabs placed in scenes). HUD views loaded by `AssetReference` and Localization tables may be; add Addressables only when the project already uses it for those.

## Audit (read-only)
`py -I <skills>/config-and-factory-authoring/scripts/config_registry_audit.py [--no-fail] <unity-project>` reports: asset in a feature folder that no singleton factory references (`unregistered-config`), duplicate id-like fields, unassigned prefab/sprite/thumbnail fields, pool prewarm > max. WARN-level hints: Audio and Pool folders are skipped, and an asset referenced only by prefabs or scenes shows as unregistered. Pair with `framework_inventory.py`.
Not covered (needs the Editor): pool prefab lacking `PoolPrefabItem`, scene missing from Build Settings.

## Done check
Entry asset exists, Factory references it, a runtime consumer reads it through `Factory_X.Member`, Console empty after refresh.
