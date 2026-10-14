# Scenario: analytics-events-taxonomy

**Prompt:** Log when the player claims a quest.

**Expected:** Adds quest_claim to the taxonomy doc first, then logs via the facade with the allowed params.

**Must not:** Invents ad-hoc event names in code.
