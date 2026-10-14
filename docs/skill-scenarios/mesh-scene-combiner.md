# Scenario: mesh-scene-combiner

**Prompt:** Combine all static props in the stage into few draw calls.

**Expected:** Editor bake groups by material, budgeted runtime combine, excludes dynamic objects, readable source meshes, reports before/after.

**Must not:** Combine moving or toggled objects.
