# Scenario: scene-teardown-safety

**Prompt:** Switching modes throws MissingReferenceException from OnDisable.

**Expected:** Unity-null guard at the owner, skip work on unload, one EventSystem/AudioListener, repeated scene-flow test with assertions.

**Must not:** Wraps the exception in try/catch, Instantiates in OnDisable, leaves DontDestroyOnLoad popups alive.
