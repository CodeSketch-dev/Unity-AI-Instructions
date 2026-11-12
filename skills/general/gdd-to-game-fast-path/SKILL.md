---
name: gdd-to-game-fast-path
description: "Thin ordered playbook from GDD to playable build with the fewest tokens: first-30-minutes checklist, skills per phase, gates, what to skip, common pitfalls. Use when kicking off a clone or when the next step is unclear."
---

# GDD to game, fast path

An index, not a copy. Detail lives in the linked skills. `clone-pipeline` and `game-orchestrator` own the phases.

## First 30 minutes
1. Read project AGENTS.md, `docs/feedback-notes.md` tail, `git status`; check Editor/MCP connection and a clean compile (`unity-mcp-workflow`).
2. GDD present and linted (`gdd-lint`); else `gdd-intake`. Map genre (`genre-playbooks`) and write the plan once (`spec-then-plan`).
3. Confirm framework version (`framework-version-map`) and foundation (`house-style-foundation`). Reuse existing assets (`asset-transfer-closure`).

## Order of work
foundation -> core loop playable (`clone-feature-recipes`, `config-driven-feature`) -> economy/balance (`auto-balance-loop`) -> UI (`ui-builder`, `ui-validator`) -> polish (`game-feel-polish`, `ambience-layers`, `night-lighting-mobile`) -> QA (`senior-tester`, `qa-playmode-smoke`) -> perf (`mobile-perf-audit`) -> release (`mobile-build-release`).
Each step ends at `done-means-wired`: wired, compiled, exercised in Play.

## Token savers
- Load one skill per phase; pass paths, not pasted content; ask subagents for conclusions (`token-efficient-workflow`, `agent-team-protocol`).
- File-lane work in parallel; Editor work serial and batched.
- Skip: re-reading unchanged files, full-scene dumps, screenshots before the gate needs them.

## Pitfalls seen in real runs
- A compile blocker left by one agent stalls everyone: write whole files, compile under the lock.
- Lock contention and idle waiting: batch Editor work into one session per agent.
- Long Editor sessions drift: save, reload from disk before saving again.
- Stale saves and blocking popups ruin tests: back up saves, claim popups first (`playmode-driver-recipes`).
- Teardown errors appear only after repeated mode switches (`scene-teardown-safety`).
