# Scenario: camera-occlusion-fade

**Prompt:** Props block the player view; fade them.

**Expected:** Registered list, segment-vs-bounds tick, hysteresis, shared transparent twin material, pooled reset, pure-logic tests.

**Must not:** Raycasts every frame, uses renderer.material instances, leaves pooled objects faded.
