# Scenario: recipe-gacha-box

**Prompt:** Add a gem-priced mystery box.

**Expected:** Deducts before open, rolls once, guards double-open, wires events.

**Must not:** Rolls in the animation callback so a quit mid-animation loses the reward.
