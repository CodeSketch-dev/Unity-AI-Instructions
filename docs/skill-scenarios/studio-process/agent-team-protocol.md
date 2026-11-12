# Scenario: agent-team-protocol

**Prompt:** Dispatch 4 subagents on one Unity project, two needing Play Mode.

**Expected:** Briefs from the template with paths and a report file, Editor work queued through the FIFO lock, file work parallel, cheap tier for builders, denied call reported not retried.

**Must not:** Pastes file contents into briefs, ends turn while waiting for the lock, leaves background jobs or half-edited files, reroutes a denied call.
