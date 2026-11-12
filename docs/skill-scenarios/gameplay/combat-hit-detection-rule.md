# Scenario: combat-hit-detection-rule

**Prompt:** Make the sword hit enemies in front.

**Expected:** Impact-time NonAlloc overlap with buffer 32, layer mask, squared range, cone dot, no weapon collider.

**Must not:** Enable a collider every frame or allocate lists per swing.
