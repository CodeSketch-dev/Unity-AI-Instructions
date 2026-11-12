# Scenario: procedural-mesh-generator

**Prompt:** Generate the obby platforms from a JSON spec.

**Expected:** PartSpec list, 24-vertex blocks, stud-scale uv0 snapped to integer studs, idempotent output folder, caps and count report.

**Must not:** Hand-model FBX or run unbounded loops.
