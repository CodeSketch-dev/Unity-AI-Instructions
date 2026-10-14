---
name: editor-tool-authoring
description: Write safe, idempotent, chunked Editor tools (bakers, builders, installers) run via MCP, with guards, file results and saved scenes. Use for any script that generates/mutates many objects or assets, or after a hang/duplicate/lost-scene.
---

# Editor tool authoring

Generators that "just work once" are the most dangerous code in a Unity project: an unguarded loop or a mass instantiate can hang the Editor (one run reached ~31 GB RAM and lost unsaved work), and MCP calls that time out are **retried**, so non-idempotent scripts run twice. Write every tool to be safe to run again, in small pieces.

## Rules for the tool
1. **Idempotent**: running it twice yields the same result. Identify its own output (a named root, a marker component, a naming convention) and remove or update it first instead of adding a second copy. Example failure: stale compile + re-run created duplicate shop stalls.
2. **Chunked**: one logical unit per call (one map segment, one prefab, one zone). Long calls time out and get retried; short, independent calls recover cleanly.
3. **Guarded**: validate inputs before work (positive lengths, counts under a hard cap, asset exists). Cap loop iterations and total created objects; abort with a clear message instead of looping. Estimate cost first (e.g. `renderers x materials`) and refuse above a budget.
4. **No dangerous API shortcuts**: never `PrefabUtility.InstantiatePrefab` on a *child* of a nested prefab asset (it can instantiate the whole root and multiply the scene); don't mass-instantiate objects whose `OnEnable` builds materials/meshes (bake/combine them instead; see `world-batching-culling`). Check what a component does in `ExecuteAlways` before cloning it hundreds of times.
5. **Source of truth vs generated output**: keep authoring data/objects as the source and generated meshes/objects as output that can be rebuilt (`Bake("Segment")`). When a builder owns content (e.g. a HUD builder that rebuilds a hierarchy), change the **builder** and re-run it; manual edits to the output get deleted on the next build.
6. **Assets**: when updating a generated mesh/asset, delete and recreate it, then reassign references; overwriting in place (e.g. CopySerialized) can leave a stale GPU copy even in Play Mode. Mark generated big objects non-Static if static batching would re-merge old data.
7. **Undo and dirty state**: use Undo where interactive; `EditorUtility.SetDirty`/mark scene dirty; save explicitly.
8. **Output**: write a short result summary (counts, ids, warnings) to a file under a logs path and return only a one-line status; the console is noisy and tool outputs get truncated.
9. **Menu entry + code entry**: expose a menu item and a static method so the tool can be run by a human or via MCP with parameters.
10. **Compile gate**: after editing the tool, wait for recompile to finish before invoking it.

## Before running through MCP
- Check Editor state: not in Play Mode (edits made in Play Mode are lost), not compiling, correct scene open, correct project. See `unity-mcp-workflow`.
- Save the scene before and after each stage.
- Another agent or the human may be using the same Editor; expect Play Mode to be interrupted by their QA, and never run a long tool while they are mid-test (`multi-agent-coexistence`).

## After running
Verify counts (renderers, materials, objects) against expectations, open the result, read the Console, save, and note any manual step the tool cannot do. Record the tool's name and parameters in the plan or notes so the result is reproducible.
