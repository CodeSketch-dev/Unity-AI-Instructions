---
name: tech-debt
description: "Inventory dead code, duplicates, oversized files and stale assets, rank by cost, remove safely with a GUID/reference scan and separate revertable commits. Use when cleaning the project or before a refactor."
triggers: tech debt, dead code, cleanup, unused assets, duplicate code, oversized file, safe delete, don dep, ma chet, xoa an toan, no ky thuat
---

# Tech debt

Use for periodic cleanup. Delete only what is proven unused.

## 1. Inventory
- Dead code: types never referenced (code graph or search), unused methods, commented-out blocks, obsolete flags.
- Duplicates: two systems doing one job, copy-pasted blocks, near-identical prefabs or materials.
- Oversized: files over ~600 lines or classes with unrelated responsibilities.
- Stale assets and docs: unreferenced textures/prefabs/materials, one-off builders whose output is final, old prototypes, outdated notes.
- Risk items: per-frame allocations, missing unsubscribes, statics that survive reloads.

## 2. Rank
Score each item: cost to fix (S/M/L) x risk if left x how often it hurts. Do high pain + small cost first; park the rest in the backlog, one line each.

## 3. Safe-removal protocol
1. Search path strings, type names, `Resources.Load` names, addressable keys and reflection strings.
2. For assets: scan GUIDs across scenes, prefabs, materials, ScriptableObjects, ProjectSettings and packages (grep the `.meta` guid in text-serialized files).
3. Check tests and editor tools for references.
4. If anything references it, it is not dead; move on.
5. Delete in its own commit or change batch, apart from feature work, so it can be reverted. Never delete files others are editing.
6. Compile, read the Console, count missing scripts/references on scenes and prefabs, run the assets row of `regression-suite`.

## 4. Split oversized files
Only along existing seams (partial classes by responsibility), one type per file, no behaviour change, tests green before and after.

## Output
Items removed, items kept with reason, backlog entries, verification numbers.
