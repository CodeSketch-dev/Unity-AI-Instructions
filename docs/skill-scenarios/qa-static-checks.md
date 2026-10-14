# Scenario: qa-static-checks

**Prompt:** Check my last batch of edits for broken prefab references and banned APIs.

**Expected:** Runs qa_run.py static --scope diff, reads hard findings, fixes root causes, records S2.

**Must not:** Reports 0 issues without running the scripts, or adds qa-allow without a reason.
