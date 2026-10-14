---
name: reference-index
description: One-time searchable index of the reference projects in docs/clone-plan.md; find a prefab/script/scene/tool in one query. Use on "like the reference", before reference-port/asset transfer, or when searching big projects is slow.
---

# Reference index

References are declared per game, not hardcoded: the `References` table in `docs/clone-plan.md` (template: `clone-pipeline/assets/clone-plan.template.md`) lists each reference project's name, path, index file and what it is the source of (UI, IAP, ads, pets...). Read that table first; if a path is missing, ask once.

The team's reference projects are large (thousands of scripts and prefabs) and read-only. Scan each once into a JSON index; every later lookup takes a fraction of a second and a few lines of output.

## Build (once per reference, rebuild when it changes)
```
python -I ../project-context-map/scripts/unity_project_scan.py scan --root <ref project> \
    --out-json <indexes dir>/<name>.json --out-md <indexes dir>/<name>.map.md [--first-party Assets/_ROOT Assets/_Arts]
```
- Keep the indexes **outside** every Unity project (e.g. a shared `reference-indexes` folder) and note the folder in the global instructions or the project map, so every project and agent uses the same copies.
- The script is read-only. A 2-3k script project takes ~1 minute.
- Pass `--first-party` with the prefixes of the project's own code to rank it above vendor/sample code (without it, a vendor heuristic is used).

## Query
```
python -I ../project-context-map/scripts/unity_project_scan.py query --index <name>.json pet cage [--limit 25] [--no-vendor]
python -I ../project-context-map/scripts/unity_project_scan.py show  --index <name>.json BoardUpgradeCage
```
- `query` takes several terms (all must match, case-insensitive) and searches script paths and types, prefab paths and the classes they use, scenes, editor menu items and ScriptableObject classes. Results show kind, path, declared types and line counts; `(v)` marks vendor code.
- `show` on a class prints its definition summary and the prefabs using it; on a prefab prints the scripts it uses with their paths. This answers "what does this prefab need" before an asset transfer.

## Workflow with other skills
1. User names a feature -> `query` the likely reference(s) (try 2-3 synonyms: board/upgrade/cage; treadmill/speed).
2. `show` the prefab and its scripts -> choose what to read in full (only the few files that matter).
3. Dependency closure for the transfer: `asset-transfer-closure` (`resolve_closure.py`).
4. Compare and implement: `reference-port`. Record the paths you used in the plan or the project map's reference table.

## Notes
- The index only knows what is in files: it does not read Addressables groups or runtime-created objects. If a prefab is not found, search by script or scene name instead.
- Read-only rule still applies: never modify the reference.
- If the index looks stale (a path no longer exists), rebuild it; do not trust an old index for decisions about new reference content.
