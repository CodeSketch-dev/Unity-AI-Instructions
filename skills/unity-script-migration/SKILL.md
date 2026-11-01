---
name: unity-script-migration
description: "Use when mass-renaming or moving Unity C# scripts into a feature folder layout (Logic/<Game>/<Feature>/<Prefix>_<Feature>_<Part>.cs) without breaking scenes, prefabs, tests or saves. Ships a GUID-safe rename tool with a C# lexer."
triggers: rename scripts, move scripts, refactor folders, migrate scripts, restructure, naming convention, missing script, doi ten script, chuyen folder, cau truc script
---

# Unity script migration (GUID-safe, batch, verified)

Tools in `skills/unity-script-migration/tools/` (copy to the project's `Tools/`): `migrate_scripts.py` (rename + move), `cs_lex.py` (C# lexer), `gen_all.py` (derive mapping from `Dig<Feature><Part>` style names; adapt the regex to the project prefix).

## Loop (one batch = one feature or a handful, then commit)
1. Generate `mapping.json` `{OldClass: "<path under the game folder>/<New_Name>"}`. Names: `<Prefix>_<Feature>_<Part>`, folder `Logic/<Game>/<Feature>/`. Editor classes go to `Editor/<Game>/<Feature>/`.
2. `python migrate_scripts.py mapping.json` (dry run: prints the plan, skipped classes, string literals that mention old names). Then `--apply`.
3. Refresh Unity; compile must be clean. Fix leftovers by hand (see pitfalls). Run the full EditMode suite; open the main scene and count missing scripts (`GameObjectUtility.GetMonoBehavioursWithMissingScriptCount` over all children, also prefabs).
4. Play 5-10 s with an empty Console, then commit that batch. Never mix batches in one commit.

## What the tool guarantees
- Moves `.cs` and `.meta` together (GUID kept: scenes, prefabs, SOs keep working) and partial companions (`Class.Part.cs` -> `New.Part.cs`).
- Renames identifiers by word boundary only in code: not in strings or comments; inside interpolation holes (`$"{Old.X}"`) yes; reflection names (`"Ns.Old, Assembly"`) yes.
- Skips a class if a `.asset` file name contains it (singleton assets are loaded by name).

## Pitfalls found in practice
- A MonoBehaviour defined in a file with a different name serialises as a MISSING script when baked into a prefab. Give each MonoBehaviour its own file named after the class and re-point the YAML `m_Script` to the new GUID (text patch on `m_Script: {fileID: 0}` + matching `m_EditorClassIdentifier`).
- Naive regex string-splitting breaks on `'"'`, nested quotes in interpolation and verbatim strings and silently skips renames: use the lexer.
- Tests that reflect over type names by string (`Type.GetType("Ns.Old, Assembly-CSharp-Editor")`) skip silently via `Assert.Ignore`: compare the skipped-test count before and after.
- Odin/other binary saves store type names: add `[assembly: BindTypeNameToType("Ns.OldName", typeof(New))]` for persisted classes (a test can walk the SaveData graph and assert every renamed type is bound). Skip if the owner accepts save loss.
- Asmdef: new folders must sit under the asmdef that already owns the files; move the asmdef itself last, in one step.
- After tests, domain reload may be off: reopen the scene (`EditorSceneManager.OpenScene(path)`) before counting missing scripts; never leave a "save scene" dialog open.
- Do big Unity calls (refresh after 250+ file moves) one at a time; the MCP may time out while Unity recompiles: wait, then check console.
