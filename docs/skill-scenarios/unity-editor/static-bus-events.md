# Scenario: static-bus-events

**Prompt:** Notify shop, HUD and audio when the player dies.

**Expected:** Event_Character_Dead : IEvent with ctor payload; Subscribe/Unsubscribe paired in OnEnable/OnDisable.

**Must not:** Subscribe in Awake without unsubscribing.
