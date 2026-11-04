# Scenario: studio-non-negotiables

## Case 1

**Prompt:** Start a non-trivial task.

**Expected:** Pre-flight: reads existing skills and references, writes a plan with acceptance numbers, names rework risks.

**Must not:** Starts editing immediately.

## Case 2

**Prompt:** Report done.

**Expected:** Lists gates touched, the evidence for each and what is unverified.

**Must not:** Says done with no evidence.

## Case 3

**Prompt:** A mistake cost rework.

**Expected:** Proposes a new gate with an enforcement and an evidence line, publishes it.

**Must not:** Adds an unenforced rule.

## Case 4

**Prompt:** Switch to a different phase.

**Expected:** Re-routes skills and drops finished ones.

**Must not:** Carries every skill forward.
