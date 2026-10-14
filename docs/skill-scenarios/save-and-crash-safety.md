# Scenario: save-and-crash-safety

**Prompt:** Make saves recover from corruption.

**Expected:** Adds backup rotation, checksum, recovery path with events, and tests of truncated and empty files.

**Must not:** Deletes the corrupt file and starts over silently.
