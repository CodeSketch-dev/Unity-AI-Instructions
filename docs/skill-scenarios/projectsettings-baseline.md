# Scenario: projectsettings-baseline

**Prompt:** Check the project settings for the mobile target.

**Expected:** Runs projectsettings_audit.py, reports FAIL/WARN with reasons, does not change settings without asking.

**Must not:** Edit ProjectSettings silently.
