# Junk categories (what to look for, how it was proven, what to do)

| Category | Signal | Proof | Action |
|---|---|---|---|
| Generated meshes stored as text | `.asset` files > 5 MB starting with `%YAML` (`size_report.py` section) | guid scan: referenced vs orphan; the generating Editor tool exists and is idempotent | delete orphans (regenerable), change the generator to write binary/FBX, mesh compression on, split cells |
| Derived tool index inside Assets | folder of thousands of `.json`/`.md` from a graph/index tool, tracked in git | `git ls-files Assets \| grep <folder>`; tool can write outside Assets | `git rm -r --cached`, ignore, write output outside `Assets/` |
| Backup / test / experiment scenes | scene not in Build Settings, 0 references, names with Backup, Test, New Scene | `--scenes` category | delete (dead-proven) or move out of the repo; vendor demo scenes -> owner decision |
| Mirrored art folders | two folders with the same files (`Models` and `FBX`) | `--duplicates` (name + size + sha1) | keep the canonical one that prefabs reference, delete the zero-reference copy |
| Prefab copies per mode | the same shop/popup prefab copied once per mode, differing by a few bytes | duplicate report + diff | one prefab, data sources per mode (see `minigame-consistency-contract`) |
| Duplicate fonts | two TMP default font assets with the same name in different folders | name + size duplicates | one copy, check Resources shadowing |
| Imported sub-project in first-party folder | a vendor project with its own Scenes, Prefabs, TextMesh Pro copy under `_Game` | folder inspection | move to the vendor area or cut to the used closure |
| Unused vendor FX | pack of 1000+ prefabs, a handful referenced | closure scan from used prefabs (`asset-transfer-closure`) | keep the closure only |
| Unused packages | manifest entry with no using/asmdef/asset hit | `--packages` (static, LIKELY-DEAD at best) | remove one by one, compile, open scenes |
| Heavy transitive chain | a small package depends on ECS/burst/collections | `required_by` note in `cat_packages.csv` | replace or drop the feature that needs it |
| Stray root files | screenshots, Readme.asset, `Assets/ProjectSettings`, scratch folders (`_Tmp*`, `Backup~`) | `ls Assets` | delete after owner OK; ignore the output folder of the tool that writes them |
| Uncompressed imports | textures at 2048 everywhere, SFX decompress-on-load, models without mesh compression | `import_audit.py` | presets per folder (`import-presets`) |
| One-off Editor tools | menu items for migrations already done | menu usage review | delete after use; a tool that edits assets on every domain reload is a bug |

Order of work that paid off in practice: (1) untrack derived folders (zero risk), (2) orphan generated assets (largest MB), (3) backup/test scenes, (4) duplicates, (5) packages, (6) imports, (7) vendor trimming.
