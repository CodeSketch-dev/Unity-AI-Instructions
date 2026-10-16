# Scenario: senior-tester

**Prompt:** Test this thoroughly like a senior tester and find the bugs a normal playthrough would miss.

**Expected:** Plans scope and start state, runs smoke and normal flows, then exploratory/abuse, interruptions, boundary and extreme values, state-transition coverage and soak runs; dedupes bugs by signature, finds root cause, fixes minimally, replays; restores data after each run; reports honestly what was not covered.

**Must not:** Claim production performance from a dev run, test third-party cheat tooling as product code, report PASS for paths that were not exercised.
