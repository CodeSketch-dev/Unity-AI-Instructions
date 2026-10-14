# Scenario: recipe-add-pickup

**Prompt:** Add a coin pickup that gives 5 gems and respawns after 30s.

**Expected:** Collect subclass, IsPlayer guard, DataValue write, sfx via Factory_Audio, PrimeTween respawn stopped in OnDestroy, MCP verification.

**Must not:** Use OnTriggerEnter with GetComponent or skip verification.
