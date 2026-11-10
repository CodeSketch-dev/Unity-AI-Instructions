---
name: lean-asset-audit
description: "Use when a Unity project feels heavy or before a cleanup: measure size by folder, oversized text-serialized meshes, duplicates by hash, GUID-unreferenced assets, import settings, unused packages and tracked generated folders; ranked proof-backed delete list."
triggers: lean, heavy project, project size, repo size, big files, duplicate assets, unused assets, dead assets, dead meshes, unused packages, import settings audit, tracked generated folder, dung luong, du an nang, file thua, xoa file khong dung, asset thua, knife tower style
---

# Lean asset audit (measure, prove, then delete in batches)

Goal: a lighter project that loses nothing. Measure first, prove unused second, delete third, always in separate revertable batches (`tech-debt` owns the deletion rules, this skill produces the proof and the numbers). Never delete from a guess. Scripts are read-only and stdlib-only; run them with `python -I` from the skill folder against the project root.

## 1. Baseline (before touching anything)
1. `scripts/size_report.py --root <project> --first-party Assets/_Game Assets/_Art` : MB and file count per folder, bytes per extension, biggest files, text-serialized `.asset` over the threshold, binary scenes, Resources weight, tracked generated suspects, git pack size.
2. `scripts/import_audit.py --root <project>` : texture max sizes, missing Android override, audio load types, model compression and readable flags (from `.meta`, file-level facts only).
3. Paste both outputs into the lean report (`references/lean-metrics-table.md`). These are the "before" columns; the same commands later give "after".

## 2. Find the junk (categories in `references/junk-categories.md`)
- Generated meshes/maps saved as text `.asset` (YAML): the classic bloat, 3-5x the binary size and unreadable by grep. Store as binary assets or FBX, mesh-compressed, split large cells (no generated asset above ~20 MB or ~200k vertices).
- Derived tool output tracked inside `Assets/` (code-graph indexes, caches, exports, screenshots): untrack and ignore, never import.
- Backup, test and experiment scenes outside Build Settings; stale prefab/scene copies kept "just in case".
- Same name + same size + same sha1 copies (art mirrored in two folders, one shop prefab copied per mode, duplicate TMP default fonts shadowing each other).
- Imported sub-projects or vendor packs living inside first-party folders; vendor FX packs used for 5% of their effects.
- Unused packages and default modules in `Packages/manifest.json`; a package that pulls a heavy transitive chain (ECS, burst) for one feature.
- Oversized or uncompressed imports (see `references/import-settings-table.md`).

## 3. Prove it is dead (GUID reference index)
Run `scripts/dead_assets_proof.py --root <project> --out <reports dir> --cand <name>=<Assets/folder> --scenes --duplicates --packages --derived <Assets/folder>`.
It builds the guid -> path index from every `.meta`, scans every text-serialized file for `guid:` references, string literals in `.cs` (Resources.Load names, path strings, prefix literals), build-settings scenes, protected folders (Resources, StreamingAssets, Plugins, Gizmos), ancestor-folder references (Addressables, atlases) and binary-serialized files (byte scan). Verdicts: DEAD-PROVEN, LIKELY-DEAD, UNKNOWN, KEEP, with the note that decided it. Details and limits: `references/guid-index.md`.
Rules: only DEAD-PROVEN goes to deletion; LIKELY-DEAD and UNKNOWN go to a human; packages are never DEAD-PROVEN (native/transitive use is not provable statically).

## 4. Deletion workflow (`references/deletion-workflow.md`)
Dry-run Editor tool that reads `dead_proven.csv` and logs; re-run the proof right before the real run; delete through `AssetDatabase.DeleteAsset` (keeps metas consistent) in one commit per category; then compile, open every build scene, count missing scripts/references, check the Console, re-run `size_report.py` for the after numbers. Derived folders: `git rm -r --cached`, add to `.gitignore`, verify with `git check-ignore -v`, keep on disk.
Regenerable output: delete only when the generator is idempotent and the Editor tool that makes it is kept.

## 5. Prevent the comeback
- Budgets live in the rubric (`staged-refactor-playbook`): unreferenced first-party <= 1% of bytes, no first-party asset > 20 MB, duplicates 0, every package used, scenes <= 5 MB.
- Add the proof run to the scheduled dead-asset sweep (`git-hygiene-conventions`) and to the pre-release checklist.
- Texture/audio/model defaults are enforced by presets or an AssetPostprocessor (`import-presets`, `audio-import-and-mixer-optimization`), not by hand.

## Done check
Before/after table from the same commands, proof CSVs saved with the report, every deleted path DEAD-PROVEN, build scenes open with 0 missing scripts, empty Console, EditMode PASS/SKIP counts unchanged.

## Pitfalls
- A 0-reference GUID can still load by string: `Resources.Load`, `Addressables` keys, folder loads, `AssetDatabase.LoadAssetAtPath` in Editor tools. The proof checks literals; a dynamically built path ("Biome_" + n) is caught only as a prefix literal.
- Baked-mesh and generated-art folders are loaded by BUILT paths (`dir + name + "_" + hash`), invisible to GUID and file-stem scans. Real case: 3717 baked meshes had 0 GUID refs and no stem in code, yet deleting them nulled 8532 MeshFilters in one scene. Rule: a folder whose path literal appears in an Editor/runtime script (baker `MESH_DIR`, generator output dir) is NEVER deleted on GUID proof alone.
- Delete-then-measure gate (mandatory for those folders): count null `MeshFilter.sharedMesh`, null sprites/materials and missing scripts over ALL scenes before and after (script-execute over every scene), delete ONE group per refresh, compare, restore at once (`git checkout -- <paths>`) if any count rises. Play of the Home scene alone proves nothing: a minigame scene can break.
- Binary-serialized scenes hide references from text scans: the script byte-scans them but you must validate the byte layout on one known GUID; convert such scenes to Force Text anyway.
- "Same name, same size" is a hint, the sha1 is the proof; keep one canonical copy and repoint nothing by hand (delete the copy with 0 references).
- Vendor folders: unreferenced does not mean ours to delete; trim a vendor pack to its used closure (`asset-transfer-closure` resolver) or leave it.
- Library size and import time change after deletion, not git pack size: a history rewrite is a separate owner decision.
- Measure on the same machine state; say plainly when RAM or load-time effects were not measured on a device.

See also: `tech-debt`, `import-presets`, `repo-hygiene-gitignore-audit`, `asset-transfer-closure`, `profiling-evidence`.
