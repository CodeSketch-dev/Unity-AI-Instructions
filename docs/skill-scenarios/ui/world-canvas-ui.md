# Scenario: world-canvas-ui

**Prompt:** Copy a pixel-layout shop board onto a world sign with 12 slots.

**Expected:** Strips layout groups, scales px by k with pixelsPerUnitMultiplier 1/k, capacity >= 12 with the largest items.

**Must not:** Truncate slots, leave layout groups, trust saved-scene rects.
