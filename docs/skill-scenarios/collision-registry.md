# Scenario: collision-registry

**Prompt:** Add a speed-boost pad the player can touch.

**Expected:** Checks framework version, makes an OptCollisionRegister subclass implementing ICharacterCollidable with base calls, no OnTriggerEnter/GetComponent.

**Must not:** Write a raw OnTriggerEnter that calls GetComponent<Character>.
