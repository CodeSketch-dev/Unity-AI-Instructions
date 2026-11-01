---
name: unity-script-migration
description: "Use when mass-renaming, splitting or moving Unity C# scripts into a feature layout (Logic/<Game>/<Feature>/<Prefix>_<Feature>_<Part>.cs), converting events to StaticBus, or moving scripts under asmdefs, without breaking scenes, prefabs, tests or saves. Ships GUID-safe tools."
triggers: rename scripts, move scripts, split classes, one class per file, refactor folders, migrate scripts, restructure, naming convention, missing script, staticbus, doi ten script, chuyen folder, cau truc script, tach class
---

# Unity script migration (GUID-safe, batch, verified)

Tools: `skills/unity-script-migration/tools/` (copy to the project's `Tools/`). They were written for a project whose game prefix is `Dig` and whose scripts live under `Assets/_Game`; for another game change the constants at the top of each file (`SEARCH_ROOTS`/`SCRIPTS`/`ROOT`, the `Dig_` prefix in `new_name()` and `gen_all.py`, `Event_Dig_` in `events_to_bus.py`). Test templates: `templates/Dig_TestBus.cs`, `templates/IDig_Source.cs`.

| Tool | Does |
|---|---|
| `migrate_scripts.py map.json [--apply] [--strings-only]` | rename classes + move `.cs/.meta` together (GUID kept), rewrite identifiers in code only (lexer), interpolation holes, reflection strings `"Ns.Old, Asm"`; skips classes that have a same-named `.asset`; moves partial companions |
| `cs_lex.py` | C# lexer used by the others (code vs strings/comments/chars) |
| `gen_all.py` | build `map.json` from `Dig<Feature><Part>` names |
| `split_types.py <folder> [--apply]` | one type per file; never moves `partial`; skips files with several namespaces / `#if` / `#region`; keeps the old name on collision; refuses to overwrite |
| `fix_unresolved.py [--apply]` | heal leftover `DigXxx` identifiers by matching normalized names of declared types (only identifiers starting with `Dig`) |
| `events_to_bus.py <facade.cs> <EventFolder> [--apply]` | facade `public event Action<..>` -> `Event_*` classes (with `Source`) + `StaticBus.Post`, rewrites method-group subscribers |
| `tests_to_bus.py errors.txt` | rewrite test lambdas that subscribed to removed facade events into `Dig_TestBus.On<E>(source, e => ...)` (input = compile-error lines) |
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
Verified on a 900-file project: GUID-safe moves, lexer renames, one-type-per-file splitting, StaticBus conversion of 4 facades, editor asmdef split; EditMode green after each step, scene and prefabs 0 missing scripts, 5 s Play clean. Not verified: other projects, Linux/macOS paths, PlayMode test suites (only a 5 s Play smoke), the tools' behaviour on `#if`-heavy files (they skip them).
