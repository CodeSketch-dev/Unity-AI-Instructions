---
name: rule-editor-tool-safety
description: Hard safety rules for Editor generators, bakers and MCP-driven scripts (iteration caps, nested prefabs, saves, NavMesh persistence, null checks). Use before writing or running any script that mutates many scenes, prefabs or assets.
---

# Editor tool safety

Each rule traces to a real incident (report 11, VERIFIED in notes). Pairs with `editor-tool-authoring` (how to build tools) - this is the short blocklist.

1. **Never `PrefabUtility.InstantiatePrefab` on a nested-prefab child** (30 GB hang, unsaved session lost).
2. **Cap every loop** with an iteration limit and a time/size guard (a runaway used about 31 GB).
3. **Idempotent and keyed by name or GUID**; running twice changes nothing. Naming: `_Builder`, `_Wiring`, `_Generator`, with "Only" menu variants for partial runs.
4. **One unit of work per MCP call** (one segment, one prefab); `MarkSceneDirty` + `AssetDatabase.SaveAssets`; save the scene after each stage.
5. **Mesh assets**: delete and recreate rather than overwriting in place (stale GPU mesh); reload the scene after meshes change on disk.
6. **NavMesh**: `NavMeshAssetManager.instance.StartBakingSurfaces(...)` and then save the scene; `BuildNavMesh + SaveAssets` did not persist (failed twice). Verify the asset is referenced; rebake after moving zones.
7. **Print a count report on every run** (created / skipped / failed) and return results via a file for big outputs; never dump raw scene text into the context.
8. **Destroyed Unity objects**: do not use `?.` or `??` on `UnityEngine.Object` (fake-null); wrap cross-feature side effects in try/catch so the next effect still runs.
9. **Do not edit vendor/package files** or another agent's claimed file; claim first (`multi-agent-coexistence`).
10. **Backups**: back up the dev save before mock purchases; never delete assets to make an error disappear.
11. Tools that write into a reference Unity project need the user's approval first.
