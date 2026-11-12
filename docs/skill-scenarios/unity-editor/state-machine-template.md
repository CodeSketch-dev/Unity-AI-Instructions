# Scenario: state-machine-template

**Prompt:** Give the boss phases Idle, Charge, Stunned.

**Expected:** Enum + IStateMachine state classes, explicit initial state, single State property, Dispose in OnDestroy.

**Must not:** Boolean flags or reading PreviousState.
