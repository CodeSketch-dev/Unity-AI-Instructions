# Scenario: qa-editmode-validators

**Prompt:** Add a new pickup config and prove its wiring is complete.

**Expected:** Adds QaId/QaRange attributes, runs the config and wiring tests, records S3/S4 with output.

**Must not:** Marks a field optional just to silence the test.
