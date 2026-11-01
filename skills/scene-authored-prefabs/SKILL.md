---
name: scene-authored-prefabs
description: "Use when adding any manager, system, world piece, player/camera/GUI stack, skybox or UI page to a Unity project, or when naming scripts/folders/events: prefab in Assets/_Game/Prefabs/<Feature>/ placed in the scene (never runtime-spawned), Knife Tower folder and naming layout, StaticBus events."
triggers: prefab, scene, manager, singleton, spawn, instantiate, resources.load, folder, structure, naming, hierarchy, skybox, bootstrap, staticbus, event, asset suffix, keo prefab, dat ten, cau truc, shop item, scrollrect
---

# Scene-authored prefabs and house layout (Knife Tower style)

Why: the owner vibe-codes. Everything must be findable and hand-tunable in the Hierarchy or Prefab Mode; a runtime-spawned object is invisible to them. Prefer SketchEngine facilities (StaticBus, MonoCached*, DataBlock, pools, Opt* collision, audio, popup) over custom code: it is the owner's own framework, Knife Tower is built entirely on it.

## Rules
1. Every manager/system/world piece = a GameObject with its scripts and serialized references, saved as a prefab in `Assets/_Game/Prefabs/<Feature>/<Name>.prefab`, and its instance is placed in the scene. No `new GameObject`, `AddComponent`, `Instantiate` or `Resources.Load` to create managers at runtime. Runtime code only wires or uses existing scene objects. Legit runtime spawns: pooled FX, projectiles, pets, floating text, list items of a UI page.
2. Every scene root is a prefab instance (Player, Player_GUI, Player_Camera, Environment, World, Game managers); sub-pieces (SellPad, CageRing, ...) are nested prefabs.
3. Do not rename scene objects that code finds by name. Tunables are `[SerializeField]` on the prefab, never hard-coded.
4. Converting an existing scene object: FIRST search for an existing prefab of the same thing (`AssetDatabase.FindAssets`; Editor bakers often write one) and for missing scripts (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount`). Then `PrefabUtility.SaveAsPrefabAssetAndConnect(go, path, InteractionMode.AutomatedAction)` turns the same instance into the prefab instance. One big root per call (a call that scans the whole scene can time out). Save the scene, reopen it, count missing scripts again, Play 5 s with an empty Console.
5. Known pitfall: a MonoBehaviour defined in a file with another name is saved as a missing script. One MonoBehaviour per file, file name == class name.

## Folder layout
- `Assets/_Game/` everything that ships: `Scripts/{Core,Data,Editor,Event,Factory,Logic,Utilities}`, `Prefabs/<Feature>`, `Scenes`, `Configs/<Feature>`, `Audios/{BGM,Sfx}/<Feature>`, `Materials`, `Resources` (singleton assets only), `Fonts`, `Localization`.
- `Assets/_Art/{2D (GUI, Atlas, Textures), 3D, Fx, Shader, Skyboxes}` source art; third-party packs in `Assets/Packages Fx/<Vendor>` and `Assets/Packages Required`, never inside `_Game`.
- `Scripts/Editor/<Game>/<Feature>/` is a sibling of `Logic` and has its own editor-only asmdef (an `Editor` folder under a runtime asmdef would compile into the runtime assembly). Easy to delete or exclude from builds.
- Check `.gitignore` before naming a feature folder `Tutorial`, `HowTo`, `Examples` (Unity templates ignore them).

## Script naming (counted on Knife Tower, 579 Logic files)
- `Logic/<Feature>/<Feature>.cs` and `<Feature>_<Part>.cs` (`Character`, `Character_Dead`, `AI_Renderer`); one extra folder level for sub-features. A game owns a prefix: `Logic/Dig/Rush/Dig_Rush_Clock.cs`. Namespace flat (`Game`), one type per file, file name == class name.
- Suffixes: `_Asset` ScriptableObject entry (21 files, assets in `Configs/<Feature>/`), `Factory_<X>` ScriptableObjectSingleton registry, `Data_<X>` DataBlock, `_Config`, `_Static` helpers, `_Type` enums, `_Component : MonoCached` base resolving the owner (most sub-parts derive from it), `_Manager`/`_Master`, `_State_<Name>`, `_Item/_Tab/_Popup/_Button/_UI/_GUI`, `_Detector`, `_Updater`, `_Receiver`. Interfaces `I<Name>`.
- Events: `Event_<Feature>_<Noun>_<Verb>.cs` in `Scripts/Event/<Feature>/`.

## Events: StaticBus recipe (verified in a real project)
- Cross-class notifications: `public class Event_X : IEvent` (payload by constructor, read-only properties); `StaticBus<Event_X>.Post(new Event_X(...))`; subscribe and unsubscribe symmetrically (OnEnable/OnDisable or Awake/OnDestroy); handler `StaticBus_<Name>(Event_X e)`.
- Namespace `SketchEngine.Patterns.Observer`, assembly `SketchEngine.Patterns` (add to every asmdef that posts or subscribes).
- Pure logic classes driven directly by unit tests may keep plain C# events.
- Several instances of one facade can exist in tests: events raised by a facade carry `object Source` (`IDig_Source`), and tests subscribe with `Dig_TestBus.On<E>(source, handler)`, which filters by source and unsubscribes when the next test starts (static buses otherwise leak between tests). Templates in `skills/unity-script-migration/templates/`.

## UI pages (Shop as the model; verified by reading Knife Tower prefabs through MCP)
- Page prefab: script on the root with `[SerializeField] ScrollRect _scrollRect; GameObject _itemPrefab;`, hierarchy `Root/Board/Content_BG/ScrollRect` + `Preview/...`, buttons `Button_*`. The page instantiates one item prefab per entry.
- Item prefab: root is the Button (`Image + Button + UIPressPrimeTween + AudioButtonSfx + <Feature>_Item`), children by role `Frame_Selected/Locked/Unlocked/Equipped`, `Thumbnail`, `Lock/Icon`, `Notify`, `Btn_*`, `Text_*`; text has `Localize_TMP_Font` (+ `Localize_TMP_Text` when localised).
- Serialized field prefixes `_btnX/_txtX/_imgX/_goX/_frameX`. Prefab folders mirror features (`Prefabs/Shop/{All,Boost,Skin,Sound,Trail}`). Knife Tower uses regular prefabs for items; prefab variants for items that differ only by art or labels are the owner's preference, not something verified in Knife Tower.

## Done check
Prefab exists once (no duplicate baked copy), scene instance is a prefab instance, scene saved, 0 missing scripts, compile clean, EditMode green, Play 5 s with an empty Console.
