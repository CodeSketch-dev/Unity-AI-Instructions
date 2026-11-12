# Subagent brief template (copy, fill, send)

**Goal:** one sentence + definition of done (wired, compiled, exercised).
**Read first (paths only):** project AGENTS.md, docs/feedback-notes.md tail, <spec/ledger paths>, <files you own>.
**You own:** <files/scenes/prefabs>. **Do not touch:** <everything else>, ProjectSettings, other agents' claims.
**Rules:** English files; terse; no commit/push; Editor only under the lock (scripts/editor_lock.sh); clear blocking popups with a real tap before any test; write whole files once; compile + Console clean before release; on a denied call stop and report it.
**Process:** inspect -> plan in 5 lines -> implement -> compile -> verify with evidence -> restore saves/timeScale -> release lock.
**Report:** docs/reports/<task>.md (status, files, evidence, unverified, reload notes). Final answer <= 10 lines: status + report path.
**Model:** <tier>; escalate to the strong tier only for balance/architecture questions.
