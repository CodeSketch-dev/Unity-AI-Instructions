---
name: project-structure-layout
description: "Use when creating or refactoring a Unity project's folder layout: Assets/_Game buckets (Core, Data, Editor, Event, Factory, Logic), namespaces, type and file suffix naming, asmdef policy, vendor folders, Resources, single Quality level, gitignore traps. Includes a layout audit script."
triggers: structure, folder layout, folders, project layout, namespace, naming, suffix, buckets, asmdef, assembly definition, gitignore, file name, one type per file, knife tower style, kt style, cau truc, thu muc, dat ten, dat ten file, bo cuc, quy uoc ten
---

# Project structure and naming (the studio standard)

Why: the owner and any new developer must find a feature by name in under a minute. One obvious folder per feature, one type per file, one naming grammar. Prefer SketchEngine facilities; check the installed package API before writing framework code.

## 1. Assets layout
```
Assets/
  _Game/            first-party content only
    Audios/{BGM,Sfx}/<Feature>   Configs/<Feature>   Fonts   Localization   Materials
    Prefabs/<Feature>/           Resources/ (framework singleton assets only)   Scenes   Textures (only if real content)
    Scripts/{Core,Data,Editor,Event,Factory,Logic,Utilities}
    Tests/{EditMode,PlayMode}    (each with its test asmdef)
  _Art/{2D,3D,Fx,Shader,Skyboxes}     source art, one root, one spelling
  Packages Fx/<Vendor>   Packages Required/<Vendor>   Plugins   <vendor SDK roots>   never inside _Game
  Settings/ (URP assets, volume profiles)
```
- Feature content lives under `Prefabs/<Feature>`, `Configs/<Feature>`, `Audios/<BGM|Sfx>/<Feature>`; never a feature-named folder at the `_Game` root. Add a folder only when it has real content.
- Imported sub-projects and vendor packs stay outside `_Game`; keep only the used closure (`asset-transfer-closure`).
- `Resources/` holds only the framework's singleton assets and SDK config, in the folder the installed framework loads from (read the package; SketchEngine uses its own `Resources/<framework folder>/ScriptableObjectSingletons`). No prefabs, no content.
- One Quality level; tiering at runtime by a device policy over two URP assets (`device-tier-policy`). Source art, tool output and screenshots never land in `Assets/` root (see `references/do-not-copy.md`).
- Folder spellings are fixed: `Audios`, `Materials`, `Resources`, `_Art`, `Skyboxes`. No near-duplicates (`Audio`/`Audios`, `Material`/`Materials`, `_ARTs`).

## 2. Scripts and namespaces
- Buckets: `Core` (cross-feature low level), `Data` (`Data_*` DataBlocks), `Editor` (editor-only), `Event` (`Event/<Feature>/`), `Factory` (`Factory_*` registries), `Logic/<Feature>/` (runtime), `Utilities` (small statics). No `Common`/`Manager`/`Helpers` dumping folders.
- Runtime: flat `Logic/<Feature>/<Feature>.cs` and `<Feature>_<Part>.cs`; one extra folder level for sub-features. A minigame or mode owns a short prefix and folder: `Logic/Minigame/<Name>/<XXX>_<Part>.cs`. The Home hub is a feature too (`Logic/Home/`).
- Namespace: `Game` for first-party code, flat (never mirrors folders, no per-game namespaces). Editor tools may use `Game.Editor`. Target >= 95% of runtime files.
- One top-level type per file, file name == type name (a MonoBehaviour in a file with another name bakes into prefabs as a MISSING script). Tiny enums/events included. Partial classes only for generated code.
- Runtime code never `using UnityEditor` outside `#if UNITY_EDITOR`; editor code lives in `Editor` folders.
- Files stay under ~400 lines; split along seams (partial by responsibility is the last resort).

## 3. Assemblies (ruling D2)
- First-party code compiles in the default assemblies (`Assembly-CSharp`, `Assembly-CSharp-Editor`). No custom runtime asmdef unless it carries a real `references` list (SketchEngine, UniTask, TMP, PrimeTween, Addressables, Localization) and a reason (a big isolated module, a shared package). An asmdef with empty references breaks the moment a file uses a framework namespace.
- Editor code goes in `Scripts/Editor/<Feature>/` (compiles to the editor assembly); keep runtime free of editor symbols.
- Test asmdefs ARE required: `Tests/EditMode` and `Tests/PlayMode`, referencing the default assemblies via `Assembly-CSharp` auto-reference or an explicit list; both run in the regression gate.
- If a legacy asmdef exists, do not split further; fold it back when it blocks tools (`unity-script-migration` moves the asmdef with its `.meta`).

## 4. Naming grammar
Suffix and prefix table with counts: `references/naming-suffix-table.md`. Short form: `Data_<X>`, `Factory_<X>`, `Event_<Feature>_<Noun>_<Verb>`, `<Feature>_Asset` (ScriptableObject entry, assets in `Configs/<Feature>/`), `<X>_Static`, `<X>_Type` (enum), `<X>_Manager`/`<X>_Master`, `<X>_State_<Name>`, `<X>_Item/_Popup/_Tab/_Button`, interfaces `I<Name>`. Private fields `_camelCase`, constants `UPPER_SNAKE`, private methods without the `private` keyword. Prefabs `<Feature>_<Part>`, configs `<Feature>_<Name>`; no `New`, `Copy`, `Final`, `_old`, `Backup`, `test`, `tmp` in names. Scenes: `scene-naming-conventions`; UI nodes: `ui-naming-conventions`.

## 5. Verify
1. `python -I scripts/layout_audit.py --root <project>` : bucket check, namespace share, file==type, one type per file, prefix drift, `UnityEditor` leaks, long files, asmdef policy, test asmdefs, Resources prefabs, scratch files. FAIL lines are the refactor backlog; PASS lines are the rubric evidence.
2. Per-feature counts (events, coroutines, Update, private keyword): `unity-script-migration/tools/style_audit.py`.
3. `git check-ignore -v` for every new folder (`references/layout-audit.md`).
4. After moves: compile, EditMode PASS/SKIP counts equal the baseline, 0 missing scripts, Play 5 s empty Console.

## Pitfalls
- Moving or renaming a script by hand loses GUIDs: use `unity-script-migration`.
- Template `.gitignore` globs (`Demo*`, `Tutorial*`, `Sample*`, `Example*`) swallow first-party folders: check before naming (`repo-hygiene-gitignore-audit`).
- Do not rename legacy folders just to normalise them in a live project; add the rule to new work and migrate in a staged refactor (`staged-refactor-playbook`).
- Authored scene/prefab layout rules (managers and worlds are prefabs placed in the scene) are in `scene-authored-prefabs`; the code pattern table is in `house-code-patterns`.
