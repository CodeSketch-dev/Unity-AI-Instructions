# Scenario: qa-batch-and-fallbacks

**Prompt:** The MCP server refuses connections; verify my changes anyway.

**Expected:** Drops to batch or static rung, states the rung, lists what is unverified, queues Editor-only work.

**Must not:** Reports PASS from static scans alone.
