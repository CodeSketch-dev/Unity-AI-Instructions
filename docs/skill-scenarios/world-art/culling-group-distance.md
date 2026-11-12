# Scenario: culling-group-distance

**Prompt:** Hundreds of floating world-text labels cost CPU.

**Expected:** CullingGroup with spheres set once, onStateChanged toggling TMP enabled, dispose in OnDestroy, exclusion for always-visible text.

**Must not:** Per-frame distance loop.
