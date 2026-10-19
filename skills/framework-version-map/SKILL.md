---
name: framework-version-map
description: Identify whether a Unity project uses CodeSketch (v1) or SketchEngine (v2) and map APIs between them. Use before writing any code against the in-house framework, or when porting code between projects.
---

# Framework version map

CodeSketch and SketchEngine are ONE framework in two versions (report 01). Wrong-version API is the most common compile error, so detect first, then code.

## Detect (30 seconds)
1. Read `Packages/manifest.json`: `com.codesketch` = v1 and `com.sketchengine` = v2. Package URLs, revisions, and versions vary by project. Run `py -I <skills>/framework-version-map/scripts/framework_api_grep.py <project> [symbol]` for the resolved package dir.
2. Open the package source in `Library/PackageCache/<pkg>@*/Runtime` to confirm any API you are unsure about. Never invent an API from the other version.
3. Check existing `using` lines in nearby game files; the project's own namespace wins.

## Delta you must respect (report 01, VERIFIED by reading both trees)
| Concept | v1 CodeSketch | v2 SketchEngine |
|---|---|---|
| Namespace | `CodeSketch` | `SketchEngine` |
| Debug | `CodeSketchDebug` | `SketchDebug` |
| DataBlock accessor | `Data_X.Instance` | `Data_X.INSTANCE` (only DataBlock; singletons keep `Instance`) |
| Utilities | `Utils*` | `Utility*` |
| Audio enum | `AudioType` | `SketchAudioType` |
| Haptics | `Haptic*` | `Taptic` |
| Mono base | `MonoBase` dispatches `Tick`/`LateTick`/`FixedTick`; `MonoCached` is cache-only | `MonoCached`/`MonoCachedOpt`; inspect the project's tick owner before relying on hooks |
| Collision register | generic `OptCollisionRegister<T>` | non-generic, owner implements any interfaces |
| Singleton asset folder | `Resources/CodeSketch/ScriptableObjectSingletons/` | `Resources/SketchEngine/ScriptableObjectSingletons/` |
| Save | on pause/quit, sync write | + debounced autosave 2 s, atomic write, `.bak` recovery |
| Data preload | hand-written `DataBlockPreloader` | automatic `DataBlockWarmup` |

Do not infer optional packages from the framework version. Verify Odin, tween, async, Addressables, and localization dependencies from the target manifest and nearby code.

## Porting v1 -> v2
Treat this table as a review checklist, not a conversion recipe. Confirm every referenced symbol in the target package and update each file deliberately; some project code shadows framework bases or keeps compatibility wrappers. Never mass-replace namespaces, base classes, collision generic arguments, or singleton paths. Compile through Unity MCP after each focused migration batch.

## Traps
- A project may shadow a framework class (knife-tower defines its own `Game.MonoCached`). Check which one a file's `using` resolves to; do not copy the shadow into new projects.
- Default from reports 01; override when the installed package differs.
