# Scenario: map-chunk-prefabs

## Case 1

**Prompt:** Convert a runtime-built level (from a data list) into authored content.

**Expected:** Writes an idempotent Editor tool that bakes the data into chunk prefabs placed in the scene; runtime only combines and culls; follows conversion-checklist.md.

**Must not:** Keeps a runtime spawner or builds cubes from records at load.

## Case 2

**Prompt:** A stage has 5000 small boxes.

**Expected:** Merges adjacent same-material boxes with an Editor tool at authoring time, recounts renderers and SetPass, keeps colliders and tags.

**Must not:** Only enables dynamic batching or combines moving parts.

## Case 3

**Prompt:** Add level selection to Home.

**Expected:** Uses a selection asset per level (scene name, thumbnail, load type) listed in a factory; Home spawns item prefabs from it.

**Must not:** Hardcodes level names in the Home script.

## Case 4

**Prompt:** Doors, treadmills and fading platforms on a stage.

**Expected:** Marks them with the skip tag and keeps them out of the combiner.

**Must not:** Combines them with the static geometry.
