# Scenario: mono-singleton-template

**Prompt:** Add a manager that must exist once and survive scene loads.

**Expected:** MonoSingleton with PersistAcrossScenes, base.Awake/OnDestroy, HasInstance in teardown.

**Must not:** Use SafeInstance everywhere or forget base calls.
