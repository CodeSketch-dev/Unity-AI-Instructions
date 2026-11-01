---
name: unity-script-migration
description: "Use when mass-renaming, splitting or moving Unity C# scripts into a feature layout (Logic/<Game>/<Feature>/<Prefix>_<Feature>_<Part>.cs), converting events to StaticBus, or moving scripts under asmdefs, without breaking scenes, prefabs, tests or saves. Ships GUID-safe tools."
triggers: rename scripts, move scripts, split classes, one class per file, refactor folders, migrate scripts, restructure, naming convention, missing script, staticbus, doi ten script, chuyen folder, cau truc script, tach class
---

# Unity script migration (GUID-safe, batch, verified)

Tools: `skills/unity-script-migration/tools/` (copy to the project's `Tools/`). All project settings live in `Tools/migration.json` (copy `tools/migration.example.json`; keys documented in `migration_config.py`): game prefix, namespace, roots, runtime/editor/event folders. Test templates with `{{Prefix}}`/`{{Namespace}}` placeholders: `templates/Prefix_TestBus.cs`, `templates/IPrefix_Source.cs`.

| Tool | Does |
|---|---|
| `migrate_scripts.py map.json [--apply] [--strings-only]` | rename classes + move `.cs/.meta` together (GUID kept), rewrite identifiers in code only (lexer), interpolation holes, reflection strings `"Ns.Old, Asm"`; skips classes that have a same-named `.asset`; moves partial companions |
| `cs_lex.py` | C# lexer used by the others (code vs strings/comments/chars) |
| `gen_all.py <folder>` | build `map.json` from flat `<Prefix><Feature><Part>` class names (editor files go to the editor folder) |
| `split_types.py <folder> [--apply]` | one type per file; never moves `partial`; skips files with several namespaces / `#if` / `#region`; keeps the old name on collision; refuses to overwrite |
| `fix_unresolved.py [--apply]` | heal leftover `<Prefix>Xxx` identifiers by matching normalized names of declared types (only identifiers starting with `Dig`) |
| `events_to_bus.py <facade.cs> <EventFolder> [--apply]` | facade `public event Action<..>` -> `Event_*` classes (with `Source`) + `StaticBus.Post`, rewrites method-group subscribers |
| `tests_to_bus.py errors.txt` | rewrite test lambdas that subscribed to removed facade events into `<Prefix>_TestBus.On<E>(source, e => ...)` (input = compile-error lines) |
| `event_audit.py [root]` | list every public event / static Action with the OTHER feature folders that subscribe (StaticBus candidates) |
| `to_mono_cached.py <folder> [--apply]` | rebase `class X : MonoBehaviour` onto SketchEngine `MonoCached`, bare `transform`/`gameObject` -> `TransformCached`/`GameObjectCached`, instance `Tick/LateTick/FixedTick()` -> `public override` |
| `style_audit.py <root>` | per-feature counts: events, coroutines, Update(), MonoBehaviour, explicit private, #region, file != class |

## Loop (one batch = one feature or a handful; commit after each green batch)
1. COMMIT FIRST so any bad run is recoverable; `git status` must be clean for the folders you touch.
2. Generate the mapping, run the tool without `--apply` and read the plan (SKIP, COLLISION, NOTE lines).
3. `--apply`, refresh Unity, compile must be clean; fix leftovers (`fix_unresolved.py`, by hand).
4. Gates: full EditMode suite (compare PASS and SKIP counts with the baseline: reflection tests skip silently), reopen the main scene and count missing scripts on every GameObject and every prefab, Play 5-10 s with an empty Console.
5. Commit that batch alone.

## Pitfalls that actually happened
- A MonoBehaviour in a file with a different name bakes into prefabs as a MISSING script (`m_Script: {fileID: 0}`). One MonoBehaviour per file, file name == class name; repair by patching the YAML to the new script GUID.
- Regex string splitting breaks on `'"'`, nested quotes in `$"..{(a?"x":"y")}.."` and verbatim strings: use `cs_lex.py`.
- Files with two `namespace` blocks: a naive splitter copies the second block into every new file (duplicate types). Skip them.
- A `partial` piece or a type whose target file already exists: never overwrite.
- Source-scan tests (`File.ReadAllText("Assets/.../X.cs")`, `Directory.GetFiles(root)`) silently scan nothing after a move: grep tests for old paths and old class names inside strings, then re-run and compare counts.
- Tests that find editor types by `Type.GetType("Ns.T, <EditorAssembly>")` skip via `Assert.Ignore` when the assembly name changes.
- `.gitignore` templates hide folders: `Assets/**/Tutorial*`, `HowTo*`, `Examples*`. Run `git check-ignore -v <file>` for every new feature folder; commits silently lose ignored files.
- Binary saves (Odin) store type names: `[assembly: BindTypeNameToType("Ns.Old", typeof(New))]` for persisted classes; a test walking the save graph catches omissions. Optional if the owner accepts save loss.
- If a run goes wrong do not `git checkout`/`git clean` broadly: `git stash push -u -m <why> -- <paths>` is recoverable (ignored files are NOT stashed).
- A big refresh after hundreds of moves can leave the MCP unresponsive for minutes; wait for Editor.log to go idle. `ForceUpdate` reimports everything: avoid.
- Asmdef: an `Editor` folder under a runtime asmdef compiles into the runtime assembly; give editor code its own editor-only asmdef and reference the runtime one. Move the runtime asmdef (with its `.meta`) in the same step as its scripts. Add `SketchEngine.Patterns` (StaticBus) to every asmdef that posts or subscribes.
- Duplicate truth: baked prefabs written by Editor bakers may already exist elsewhere; search for them (`AssetDatabase.FindAssets`) before converting scene objects to prefabs and keep one canonical copy.

## Review status (verified vs not)
Verified on one 900-file project (a mobile Unity 6 game on SketchEngine): GUID-safe moves, lexer renames, one-type-per-file splitting, StaticBus conversion of 4 facades, editor asmdef split; EditMode green after each step, scene and prefabs 0 missing scripts, 5 s Play clean. Not verified: other projects, Linux/macOS paths, PlayMode test suites (only a 5 s Play smoke), the tools' behaviour on `#if`-heavy files (they skip them).

## Recipes added in later passes
- Coroutines -> UniTask: `IEnumerator X()` -> `async UniTask X(CancellationToken ct)`; `StartCoroutine` -> `X(_cancel.Token).Forget()`; `yield return null` -> `UniTask.Yield(PlayerLoopTiming.Update, ct)`; waits -> `UniTask.Delay(TimeSpan, DelayType.UnscaledDeltaTime|DeltaTime, cancellationToken: ct)`; `StopCoroutine` -> `_cancel.Cancel()` (also cancel in OnDisable/OnDestroy and before restarting the same job); static starters use `host.GetCancellationTokenOnDestroy()`. EditMode tests that drained an `IEnumerator` synchronously hang on `UniTask.Yield` (no PlayerLoop): give the routine a `bool spreadOverFrames = true` switch and call it with `false` plus `.GetAwaiter().GetResult()`.
- ScriptableObject entry -> `<X>_Asset`: (1) `AssetDatabase.RenameAsset` the `.asset` files first (GUID kept), (2) run `migrate_scripts.py` (it skips classes whose name is still in an asset file name), (3) patch the `Resources.Load("OldName")` / path strings with a lexer pass over string literals, (4) reload and check `Resources.Load(newName) != null`.
- Delegating to subagents: only file-only agents on DISJOINT file lists; tell them "no MCP, no git, no Unity"; the director compiles once after all return, fixes call sites outside their lists, runs the gates and commits. Do not compile while they are editing (transient errors).
- Before bulk-converting events, count cross-feature subscribers (`event_audit.py` idea: grep subscribers per feature). Knife Tower keeps object-owned C# events and uses StaticBus for cross-feature broadcasts; the receiver-name heuristics of `events_to_bus.py` can silently re-point a same-named event of another type: review its diff.
- `MonoCached*` in SketchEngine are caching helpers (transform/gameObject/rect cache, `GetCached<T>()`, virtual Tick hooks), not a central updater. Rebasing is cheap and safe (script GUIDs do not change): `TransformCached` only calls `transform` while the field is null and the Unity null check is a managed pointer compare in builds, so it beats repeated `.transform`. Pitfalls seen: (1) a plain class in the same file that has its own `Tick()` must not become `override`; (2) a nested `MonoCached` class calling an outer static `Tick(x)` now resolves to the inherited `Tick()`: qualify the call; (3) every asmdef that references your types must also reference `SketchEngine` (test and play-test asmdefs too), otherwise CS0012 floods; (4) skip files where `transform`/`gameObject` is declared as a parameter or local (the tool reports them as `conflict`).
