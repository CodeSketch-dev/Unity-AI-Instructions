# Scenario: one-material-world-shader

**Prompt:** The map has 150 materials and high draw calls; make it one material.

**Expected:** Moves per-part data to vertex channels, shared SRP-Batcher shader, alpha/skins as listed exceptions, validates with material census.

**Must not:** Use per-object MaterialPropertyBlock or per-instance material builders.
