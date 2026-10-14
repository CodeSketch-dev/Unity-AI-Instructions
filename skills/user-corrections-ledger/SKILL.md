---
name: user-corrections-ledger
description: Ledger of recurring user corrections and standing decisions with reasons, to avoid repeating past mistakes. Use at the start of a build, when planning a feature, or when the user corrects something similar to a past correction.
---

# User corrections ledger

One line per rule: rule - why - source. Read `references/ledger.md` for the full list (it is the DATA; this page is the entry point). Extend it through `feedback-notes-sync` when the user corrects something new; prune entries that are superseded.

## How to use
1. Before planning a feature, scan the ledger tags matching the work (UI, art, perf, process, economy, framework).
2. Treat each entry as a soft default with its reason. Deviate only with a stated reason and tell the user.
3. When a correction repeats an existing entry, strengthen that entry instead of adding a duplicate, and consider promoting it to a rule skill or a hook.
4. Consumers: `done-means-wired`, `ui-clone`, `reference-port`, `rule-port-not-invent`, `rule-qa-validity`, `rule-editor-tool-safety`.

## Top five (highest recurrence)
1. Port the reference exactly, never invent visuals (`rule-port-not-invent`).
2. Wire everything, compile, run in Play Mode; scripts alone are not done (`done-means-wired`).
3. Performance first: pool and bake, no per-frame work on populations (`pool-everything`, `mesh-merge-baker`).
4. Do not override the scene's lighting or strip a shader that works.
5. Balance is one loop; verify from a clean save at timeScale 1 (`rule-qa-validity`).
