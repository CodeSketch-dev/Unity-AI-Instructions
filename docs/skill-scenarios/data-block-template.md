# Scenario: data-block-template

**Prompt:** Add a saved daily-streak counter and last-claim time.

**Expected:** Creates Data_* : DataBlock with base.Init() and ??= for each field, DataValue accessors, no scene refs.

**Must not:** Use PlayerPrefs or skip base.Init().
