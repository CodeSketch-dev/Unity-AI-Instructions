# Scenario: ui-design-tokens

**Prompt:** Build a settings popup with no mockup, matching our reference game's sizes.

**Expected:** Runs ui_miner on the reference project, picks sizes from the emitted scales and inset values, still anchors to edges and respects safe area; states output are observations.

**Must not:** Treat mined numbers as hard limits or write to the reference project.
