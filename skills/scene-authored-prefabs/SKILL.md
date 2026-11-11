---
name: scene-authored-prefabs
description: "Use when adding any manager, system, world piece, player/camera/GUI stack or UI page to a Unity project: author it as a prefab in Assets/_Game/Prefabs/<Feature>/ placed in the scene (never runtime-created); scene root rules, converting scene objects, legit runtime spawns."
triggers: prefab, scene, manager, singleton, spawn, instantiate, resources.load, hierarchy, bootstrap, scene root, nested prefab, prefab variant, new GameObject, addcomponent, keo prefab, dat vao scene, shop item, scrollrect, kt style, knife tower
---

# Scene-authored prefabs

Why: the owner vibe-codes. Everything must be findable and hand-tunable in the Hierarchy or Prefab Mode; a runtime-created object is invisible to them. Prefer SketchEngine facilities (StaticBus, MonoCached*, DataBlock, pools, Opt* collision, audio, popup) over custom code, and check the installed package API first. The reference style runs the older CodeSketch v1 with the same concepts.

## Rules
1. Every manager, system or world piece = a GameObject with its scripts and serialized references, saved as a prefab in `Assets/_Game/Prefabs/<Feature>/<Name>.prefab`, and its instance is placed in the scene. No `new GameObject`, `AddComponent`, `Instantiate` or `Resources.Load` to create managers, UI pages or world content at runtime. Runtime code only wires or uses existing scene objects.
2. Scene roots are a MIX: prefab instances for the player, managers, map chunks and the persistent root; plain objects are fine for pure containers (`Stage`, `Shop`, `Decor`), the light, a BGM starter and a few one-off script roots. Keep roots <= 20 and name them; no tool-marker roots. The player GUI and the camera rig are NOT scene roots: they are nested prefabs inside the player prefab. Sub-pieces (`Treadmill`, `Shop_Stand`, `Stage_N`) are nested prefabs.
3. Do not rename scene objects that code finds by name. Tunables are `[SerializeField]` on the prefab, never hard-coded.
4. Converting an existing scene object: FIRST search for an existing prefab of the same thing (`AssetDatabase.FindAssets`; Editor bakers often write one) and for missing scripts (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount`). Then `PrefabUtility.SaveAsPrefabAssetAndConnect(go, path, InteractionMode.AutomatedAction)` turns the same instance into the prefab instance. One big root per call (a scene-wide call can time out). Save the scene, reopen it, count missing scripts again, Play 5 s with an empty Console.
5. A MonoBehaviour defined in a file with another name is saved as a missing script. One MonoBehaviour per file, file name == class name.
6. Variants: use prefab variants for families that differ only by art or numbers (skins, per-mode players, floors). Plain prefabs otherwise. Shared player/character bases may be variants; per-minigame UI and code stay separate (`minigame-consistency-contract`).
7. Edit the source prefab (Prefab Mode / `PrefabUtility`), not a scene override, unless an override is the intent.

## Legitimate runtime spawns
Pooled FX, projectiles, pets, floating text, list items of a UI page (`ui-page-item-prefab`), popups through `PopupManager.Create(prefab)` (destroyed on close), enemies and drops from a pool. Not allowed: managers, world pieces, UI pages, canvases, loaders. The one tolerated exception in the reference is a persistent overlay singleton (focus pointer) created from a factory prefab reference; new projects author it as a scene prefab under the popup canvas (`tutorial-focus-notice-hand`).

## Where things live
- Persistent services, canvases, EventSystem, loading, transition: `persistent-root-prefab`.
- Levels, maps, stages, towers as placed chunks: `map-chunk-prefabs`.
- Folder buckets, namespaces, file and type suffix naming, asmdef decision: `project-structure-layout`.
- Events (`IEvent`, `StaticBus` recipe, tests): `static-bus-events`.
- UI pages, item prefabs, ScrollRect filling, press/sfx components: `ui-page-item-prefab` (+ `ui-edit-mode-authoring`).
- Moving or renaming scripts safely: `unity-script-migration`.

## Done check
Prefab exists once (no duplicate baked copy), the scene instance is a prefab instance, scene saved, 0 missing scripts on scenes and prefabs, compile clean, EditMode counts unchanged, Play 5 s with an empty Console, `grep` of `new GameObject|AddComponent<|Resources.Load` in the touched code shows only whitelisted pooled/test uses.

## Gotchas (converting a runtime manager)
- Add a serialized reference on the Master/root, bake the manager as its child, resolve with a scene-authored lookup first, and keep runtime creation only as a fallback for Editor tests. Verify in Play that the scene instance is the one used. Details and the Editor snippet: [references/convert-runtime-manager.md](references/convert-runtime-manager.md).
- Editor builders must write prefabs (idempotent), not scene-only objects (`editor-bake-safety`).
- `.gitignore` can swallow folders named like Unity templates (`Tutorial`, `Examples`): `git check-ignore -v` every new folder.
- Provenance of the style: [references/PROVENANCE.md](references/PROVENANCE.md).
- Runtime binders (`transform.Find("Row" + x)`) must use FIXED object names, never localized text: baked children keep the language they were baked in, so a lookup built from `Localize.Get(...)` returns null in any other language, aborts the HUD initialise halfway and every later system then hits nulls. A chaos/random-tap PlayMode test run in a second language catches this class; fixed in two places in one project.

## Play is the truth (owner rule)
- Judge a map/scene in Play. Diff Edit vs Play (per path: activeInHierarchy, Renderer.enabled) after 5 s of Play; every object Play disables, hides, replaces or never uses is removed from the scene in Edit Mode (or its runtime toggle removed). Target: 0 Edit-only objects. Never leave Play-unused leftovers in the scene.
