---
name: scene-authored-prefabs
description: "Use when adding any manager, system, world piece, player/camera/GUI stack or skybox to a Unity project: build it as a prefab in Assets/_Game/Prefabs/<Feature>/ and place the instance in the scene; never spawn it at runtime. Also the folder and script naming layout."
triggers: prefab, scene, manager, singleton, spawn, instantiate, resources.load, folder, structure, naming, hierarchy, skybox, bootstrap, keo prefab, dat ten, cau truc
---

# Scene-authored prefabs and house layout

Why: the owner vibe-codes. Everything must be findable and hand-tunable in the Hierarchy or Prefab Mode. A runtime-spawned object is invisible to them.

## Rules
1. Every manager/system/world piece = a GameObject with its scripts and serialized references, saved as a prefab in `Assets/_Game/Prefabs/<Feature>/<Name>.prefab`, and the instance is placed in the scene. No `new GameObject`, `AddComponent`, `Instantiate` or `Resources.Load` to create managers at runtime. Runtime code only wires or uses existing scene objects. Legit runtime spawns: pooled FX, projectiles, pets, floating text.
2. Every scene root is a prefab instance (Player, Player_GUI, Player_Camera, Environment, World, Game managers). Nested prefabs for sub-pieces (SellPad, CageRing, ...).
3. Prefab name = object name = feature + prefix (`Character`, `Character_Death`, `Player_GUI`). Do not rename scene objects that code finds by name.
4. Tunables are `[SerializeField]` on the prefab (interval, material list, curve), never hard-coded.
5. Convert an existing scene object with `PrefabUtility.SaveAsPrefabAssetAndConnect(go, path, InteractionMode.AutomatedAction)`: the same instance becomes the prefab instance, internal refs survive. Do big roots one per call (a single call that scans the whole scene can time out), then save the scene and run a Play check with an empty Console.

## Folder layout (Knife Tower style)
- `Assets/_Game/` everything that ships in-game: `Scripts/{Core,Data,Editor,Event,Factory,Logic,Utilities}`, `Prefabs/<Feature>`, `Scenes`, `Configs/<Feature>`, `Audios/{BGM,Sfx}/<Feature>`, `Materials`, `Resources` (only singleton assets), `Fonts`, `Localization`.
- `Assets/_Art/` source art: `2D` (GUI, Atlas, Textures), `3D` (by feature), `Fx`, `Shader`, `Skyboxes`.
- Third-party art/FX packs: `Assets/Packages Fx/<Vendor>`, `Assets/Packages Required`, never inside `_Game`.
- Scripts: `Logic/<Feature>/<Feature>.cs`, `<Feature>_<Part>.cs` (`Character`, `Character_Death`, `Character_KC`, `Character_FallDetector`, `AI`, `AI_Renderer`); `Factory/Factory_<Feature>.cs` (ScriptableObjectSingleton), `Data/Data_<Feature>.cs` (DataBlock), `Event/<Feature>/Event_<Feature>_<Action>.cs` (IEvent + StaticBus). Namespace `Game` unless the project defines more.
- Moving or renaming: use `AssetDatabase.MoveAsset` (keeps GUIDs) and rename class and file together; compile and run tests after each batch.

## Done check
Prefab exists, scene instance is a prefab instance, scene saved, compile clean, Play 5 s with empty Console.

## Role suffixes (Knife Tower)
- `<X>_Asset` ScriptableObject entry (in `Configs/<Feature>/`); `Factory_<X>` ScriptableObjectSingleton registry; `Data_<X>` DataBlock; `<X>_Config` tuning; `<X>_Component : MonoCached` base that resolves the owner and is the parent of every sub-part (`Character_Dead`, `_Fx`, `_Sfx`, `_Renderer`); `<X>_Static` helpers; `<X>_Type` enum; `<X>_Manager` / `_Master`; `<X>_State_<Name>`; `<X>_Item/_Tab/_Popup/_Button/_UI`; `Event_<Feature>_<Noun>_<Verb>`.
- A game owns a prefix (`Dig_`, `SKB_`): `Logic/<Game>/<Sub>/<Prefix>_<Sub>_<Part>.cs`, e.g. `Logic/Dig/Rush/Dig_Rush_Clock.cs`.
- One MonoBehaviour per file, file name == class name. A class in a differently named file bakes into prefabs as a MISSING script.

## UI prefabs
- Page prefab (script on root: `_scrollRect`, `_itemPrefab`) spawns an item prefab per entry. Item prefab root = Button (`Image, Button, UIPressPrimeTween, AudioButtonSfx, <Feature>_Item`), children `Frame_*`, `Thumbnail`, `Btn_*`, `Text_*`. Fields `_btnX/_txtX/_imgX/_goX`. Use prefab variants for items that differ only by art/labels. Prefab folders mirror features (`Prefabs/Shop/Skin`).

## Events: StaticBus recipe (verified)
- Cross-class notifications: `Event_<Game>_<Feature>_<Noun>_<Verb> : IEvent` in `Scripts/Event/<Game>/<Feature>/`; payload via constructor, read-only properties. Post with `StaticBus<T>.Post(new T(...))`.
- Subscribe/unsubscribe symmetrically (OnEnable/OnDisable or Awake/OnDestroy); handler method `StaticBus_<Name>(Event_... e)`.
- asmdef projects must reference `SketchEngine.Patterns` (namespace `SketchEngine.Patterns.Observer`); add it to both the runtime and editor asmdef.
- Pure logic classes driven by unit tests may keep plain C# events.
- Editor scripts live in `Scripts/Editor/<Game>/<Feature>/` with their own editor-only asmdef (an `Editor` folder under a runtime asmdef would otherwise compile into the runtime assembly); tests that find editor types by reflection use `"Ns.Type, <EditorAsmdefName>"`.
