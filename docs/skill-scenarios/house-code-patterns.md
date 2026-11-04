# Scenario: house-code-patterns

## Case 1

**Prompt:** Add a persisted per-item upgrade level with a config and UI refresh.

**Expected:** Uses Data_ DataBlock records, an _Asset config in a Factory_ registry, an Event_ on StaticBus, subscribes in OnEnable and unsubscribes in OnDisable.

**Must not:** Uses PlayerPrefs, a static mutable dictionary, or a lambda subscription that is never removed.

## Case 2

**Prompt:** Write an enemy with Idle/Chase/Attack modes.

**Expected:** Uses the framework state machine with states in Logic/<Feature>/State/ and one owner transition method.

**Must not:** Scatters bool flags or writes a custom FSM.

## Case 3

**Prompt:** 100 pickups need to detect the player.

**Expected:** Registers colliders through the collision register family; the player is the single physics callback owner.

**Must not:** Adds OnTriggerEnter plus GetComponent on every pickup.

## Case 4

**Prompt:** Review a PR with new Update loops and Find calls.

**Expected:** Flags per-entity Update, Find/GetComponent in hot paths, uncancelled tasks, unpaired subscriptions, and cites the decision table.

**Must not:** Approves because it compiles.
