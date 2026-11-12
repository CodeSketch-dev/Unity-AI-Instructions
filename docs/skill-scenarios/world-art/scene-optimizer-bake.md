# Scenario: scene-optimizer-bake

**Prompt:** Make one button that bakes the stage before build.

**Expected:** Static idempotent Bake() with ordered steps, logs counts, saves once, callable via MCP.

**Must not:** Create a second copy of the scene.
