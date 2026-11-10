# Authoring checklist (create or rewrite a skill)

1. Topic exists? `skills/INDEX.md` search; merge/extend instead of a near-copy. Check `deps` of the candidate.
2. Name: lowercase-hyphen, specific (`fishnet-prediction-debug`, not `networking`).
3. Description <=300 chars: verb phrase of what it does + `Use when` + 2-3 concrete situations/words. Test mentally: would a user prompt that never names the skill still match?
4. `triggers:` 8-16 phrases a user types (EN + VI without accents). `not:` for confusable neighbours.
5. Body: ordered imperative steps, decision rules, one verification line (Console, MCP tool, test, screenshot). Link `references/x.md` only where used. Under ~100 lines.
6. Scripts: deterministic work only, `py -I`, helpful errors, documented usage in the docstring, path relative to the skill.
7. Evidence: 6+ trigger queries (incl. near-miss), a behaviour eval folder for important skills.
8. Generic: no project, game, class, or absolute local path names.

## Studio domains (priority list) and typical home
- Unity editor/MCP/QA: extend `unity-mcp-workflow`, `unity-qa-playtest`, `qa-*`.
- FishNet multiplayer: `fishnet-external-move-reconcile`, `dedicated-server-no-client-state`; new ones named `fishnet-<topic>` (prediction, transport, spawn, scene, ownership).
- Windows automation: new `windows-*` (PowerShell hooks, scheduled tasks, UI automation, batch scripts); coordinate with `computer-use` rules, no credential handling.
- Game design: `gdd-*`, `genre-playbooks`, `economy-*`, `recipe-*`.
- Software testing: `qa-*`, `senior-tester`, `regression-suite`, `test-evidence-review`.
