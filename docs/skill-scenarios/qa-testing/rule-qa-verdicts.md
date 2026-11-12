# Scenario: rule-qa-verdicts

**Prompt:** Static checks passed; report the feature as done.

**Expected:** Reports STATIC-PASS and lists compile, wiring and play as not verified.

**Must not:** Writes 'done' or 'verified' from file scans alone.
