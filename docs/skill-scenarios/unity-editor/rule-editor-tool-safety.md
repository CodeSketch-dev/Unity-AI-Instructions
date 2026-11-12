# Scenario: rule-editor-tool-safety

**Prompt:** Write an editor tool that places 500 props from JSON.

**Expected:** Idempotent, iteration cap, one segment per call, saves scene, count report, no InstantiatePrefab on nested child.

**Must not:** Unbounded loop or relying on fake-null with ?.
